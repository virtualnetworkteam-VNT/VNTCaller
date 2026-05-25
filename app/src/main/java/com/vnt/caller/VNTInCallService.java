package com.vnt.caller;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.AudioTrack;
import android.media.MediaRecorder;
import android.media.audiofx.AcousticEchoCanceler;
import android.media.audiofx.AutomaticGainControl;
import android.media.audiofx.NoiseSuppressor;
import android.telecom.Call;
import android.telecom.InCallService;
import android.util.Log;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;

public class VNTInCallService extends InCallService {
    private static final String TAG = "VNTInCall";
    private static final String BRIDGE_HOST = "192.168.10.96";
    private static final int BRIDGE_PORT = 9999;
    private static final int SAMPLE_RATE = 16000;
    private AudioRecord recorder;
    private AudioTrack player;
    private Socket socket;
    private volatile boolean running = false;

    @Override
    public void onCallAdded(Call call) {
        call.registerCallback(new Call.Callback() {
            @Override public void onStateChanged(Call c, int state) {
                if (state == Call.STATE_RINGING) answerCall(c);
                if (state == Call.STATE_ACTIVE) startBridge(c);
                if (state == Call.STATE_DISCONNECTED || 
                    state == Call.STATE_DISCONNECTING) stopBridge();
            }
        });
        if (call.getState() == Call.STATE_RINGING) answerCall(call);
        if (call.getState() == Call.STATE_ACTIVE) startBridge(call);
    }

    private void answerCall(Call call) {
        try { call.answer(0); Log.i(TAG,"Answered"); }
        catch (Exception e) { Log.e(TAG,"Answer:"+e.getMessage()); }
    }

    private void startBridge(Call call) {
        if (running) return;
        running = true;
        String num = "";
        try { num = call.getDetails().getHandle().getSchemeSpecificPart(); }
        catch (Exception ignored) {}
        final String callerNum = num;
        Log.i(TAG, "Bridge for: " + callerNum);

        final AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
        // SPEAKERPHONE ON - this is the key
        // Alias TTS plays loud through speaker
        // Cellular mic picks it up and sends to S25
        am.setMode(AudioManager.MODE_IN_CALL);
        am.setSpeakerphoneOn(true);
        // Max volume on all streams
        am.setStreamVolume(AudioManager.STREAM_MUSIC,
            am.getStreamMaxVolume(AudioManager.STREAM_MUSIC), 0);
        am.setStreamVolume(AudioManager.STREAM_VOICE_CALL,
            am.getStreamMaxVolume(AudioManager.STREAM_VOICE_CALL), 0);

        new Thread(() -> {
            try {
                socket = new Socket(BRIDGE_HOST, BRIDGE_PORT);
                OutputStream out = socket.getOutputStream();
                InputStream in = socket.getInputStream();
                out.write((callerNum + "\n").getBytes());
                out.flush();

                int minBuf = AudioRecord.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
                int bufSize = minBuf * 4;

                // MIC: captures Ryan's voice coming from S25 through speaker
                recorder = new AudioRecord(
                    MediaRecorder.AudioSource.MIC, // Use plain MIC not VOICE_COMMUNICATION
                    SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT, bufSize);

                // DISABLE echo canceller so Alias voice from speaker isn't cancelled
                int sid = recorder.getAudioSessionId();
                try {
                    if (AcousticEchoCanceler.isAvailable()) {
                        AcousticEchoCanceler aec = AcousticEchoCanceler.create(sid);
                        if (aec != null) aec.setEnabled(false);
                    }
                    if (NoiseSuppressor.isAvailable()) {
                        NoiseSuppressor ns = NoiseSuppressor.create(sid);
                        if (ns != null) ns.setEnabled(false);
                    }
                    if (AutomaticGainControl.isAvailable()) {
                        AutomaticGainControl agc = AutomaticGainControl.create(sid);
                        if (agc != null) agc.setEnabled(false);
                    }
                } catch (Exception ignored) {}

                // SPEAKER: plays Alias TTS through STREAM_MUSIC at max vol
                // STREAM_MUSIC goes through speaker loudly
                // This acoustic coupling is how hands-free works
                int playBuf = AudioTrack.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT) * 4;
                player = new AudioTrack(AudioManager.STREAM_MUSIC,
                    SAMPLE_RATE, AudioFormat.CHANNEL_OUT_MONO,
                    AudioFormat.ENCODING_PCM_16BIT, playBuf, AudioTrack.MODE_STREAM);

                recorder.startRecording();
                player.play();
                Log.i(TAG, "Bridge active - AEC off - speaker max vol");

                // Receive Alias voice and blast through speaker
                new Thread(() -> {
                    byte[] buf = new byte[4096];
                    try {
                        int r;
                        while (running && (r = in.read(buf)) > 0) {
                            player.write(buf, 0, r);
                        }
                    } catch (Exception e) { Log.e(TAG,"RX:"+e.getMessage()); }
                }).start();

                // Send mic audio to MSI (Ryan's voice captured from speaker)
                byte[] buf = new byte[bufSize];
                while (running) {
                    int r = recorder.read(buf, 0, buf.length);
                    if (r > 0) { out.write(buf, 0, r); out.flush(); }
                }
            } catch (Exception e) { Log.e(TAG,"Bridge:"+e.getMessage()); }
        }).start();
    }

    private void stopBridge() {
        running = false;
        try { if (recorder!=null){recorder.stop();recorder.release();} }catch(Exception ignored){}
        try { if (player!=null){player.stop();player.release();} }catch(Exception ignored){}
        try { if (socket!=null) socket.close(); }catch(Exception ignored){}
        try {
            AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
            am.setSpeakerphoneOn(false);
            am.setMode(AudioManager.MODE_NORMAL);
        } catch(Exception ignored){}
        Log.i(TAG,"Bridge stopped");
    }

    @Override public void onCallRemoved(Call call) { stopBridge(); }
}
