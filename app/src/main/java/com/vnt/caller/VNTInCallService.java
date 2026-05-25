package com.vnt.caller;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.AudioTrack;
import android.media.MediaRecorder;
import android.os.Handler;
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
    private volatile boolean bridgeRunning = false;

    @Override
    public void onCallAdded(Call call) {
        Log.i(TAG, "Call added: " + call.getState());
        call.registerCallback(new Call.Callback() {
            @Override
            public void onStateChanged(Call c, int state) {
                Log.i(TAG, "State changed: " + state);
                if (state == Call.STATE_RINGING) answerCall(c);
                if (state == Call.STATE_ACTIVE) startBridge(c);
                if (state == Call.STATE_DISCONNECTED || state == Call.STATE_DISCONNECTING) stopBridge();
            }
        });
        if (call.getState() == Call.STATE_RINGING) answerCall(call);
        if (call.getState() == Call.STATE_ACTIVE) startBridge(call);
    }

    private void answerCall(Call call) {
        try { call.answer(0); Log.i(TAG, "Answered"); } catch (Exception e) { Log.e(TAG, "Answer: " + e.getMessage()); }
    }

    private void startBridge(Call call) {
        if (bridgeRunning) return;
        bridgeRunning = true;
        String caller = "";
        try { caller = call.getDetails().getHandle().getSchemeSpecificPart(); } catch (Exception ignored) {}
        final String callerNum = caller;
        Log.i(TAG, "Starting bridge for: " + callerNum);

        new Thread(() -> {
            try {
                AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
                am.setMode(AudioManager.MODE_IN_COMMUNICATION);

                socket = new Socket(BRIDGE_HOST, BRIDGE_PORT);
                OutputStream out = socket.getOutputStream();
                InputStream in = socket.getInputStream();
                out.write((callerNum + "\n").getBytes()); out.flush();

                int bufSize = AudioRecord.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2;

                // VOICE_CALL captures both sides of cellular call
                recorder = new AudioRecord(MediaRecorder.AudioSource.VOICE_CALL,
                    SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufSize);
                if (recorder.getState() != AudioRecord.STATE_INITIALIZED) {
                    recorder.release();
                    recorder = new AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION,
                        SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufSize);
                }

                int playBuf = AudioTrack.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2;
                player = new AudioTrack(AudioManager.STREAM_VOICE_CALL, SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT, playBuf, AudioTrack.MODE_STREAM);

                recorder.startRecording(); player.play();

                new Thread(() -> {
                    byte[] buf = new byte[4096];
                    try { int r; while (bridgeRunning && (r = in.read(buf)) > 0) player.write(buf,0,r); }
                    catch (Exception ignored) {}
                }).start();

                byte[] buf = new byte[bufSize];
                while (bridgeRunning) {
                    int r = recorder.read(buf, 0, buf.length);
                    if (r > 0) { out.write(buf,0,r); out.flush(); }
                }
            } catch (Exception e) { Log.e(TAG, "Bridge: " + e.getMessage()); }
        }).start();
    }

    private void stopBridge() {
        bridgeRunning = false;
        try { if (recorder != null) recorder.stop(); } catch (Exception ignored) {}
        try { if (player != null) player.stop(); } catch (Exception ignored) {}
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
        try { ((AudioManager)getSystemService(AUDIO_SERVICE)).setMode(AudioManager.MODE_NORMAL); } catch (Exception ignored) {}
    }

    @Override
    public void onCallRemoved(Call call) { stopBridge(); }
}
