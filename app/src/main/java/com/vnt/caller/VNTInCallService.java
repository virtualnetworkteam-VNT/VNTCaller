package com.vnt.caller;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.AudioTrack;
import android.media.MediaRecorder;
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
    private AudioRecord recMic;
    private AudioTrack playerCall;
    private Socket socket;
    private volatile boolean running = false;

    @Override
    public void onCallAdded(Call call) {
        call.registerCallback(new Call.Callback() {
            @Override public void onStateChanged(Call c, int state) {
                if (state == Call.STATE_RINGING) answerCall(c);
                if (state == Call.STATE_ACTIVE) startBridge(c);
                if (state == Call.STATE_DISCONNECTED) stopBridge();
            }
        });
        if (call.getState() == Call.STATE_RINGING) answerCall(call);
        if (call.getState() == Call.STATE_ACTIVE) startBridge(call);
    }

    private void answerCall(Call call) {
        try { call.answer(0); } catch (Exception e) { Log.e(TAG, e.getMessage()); }
    }

    private void startBridge(Call call) {
        if (running) return;
        running = true;
        String caller = "";
        try { caller = call.getDetails().getHandle().getSchemeSpecificPart(); } catch (Exception ignored) {}
        final String num = caller;

        AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
        am.setMode(AudioManager.MODE_IN_CALL);
        // Keep earpiece - do NOT use speakerphone
        // We will play Alias voice directly to STREAM_VOICE_CALL
        // which goes to earpiece and the cellular uplink simultaneously
        am.setSpeakerphoneOn(false);

        Log.i(TAG, "Bridge starting for: " + num);
        new Thread(() -> {
            try {
                socket = new Socket(BRIDGE_HOST, BRIDGE_PORT);
                OutputStream out = socket.getOutputStream();
                InputStream in = socket.getInputStream();
                out.write((num + "\n").getBytes());
                out.flush();

                int bufSize = AudioRecord.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2;

                // Capture mic - Ryan's voice from S25 comes through earpiece
                // VOICE_COMMUNICATION = mic input during call
                recMic = new AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION,
                    SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT, bufSize);

                int playBuf = AudioTrack.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2;

                // Play to STREAM_VOICE_CALL - this stream feeds into the cellular
                // call uplink AND the earpiece
                playerCall = new AudioTrack(
                    AudioManager.STREAM_VOICE_CALL, SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT,
                    playBuf, AudioTrack.MODE_STREAM);

                recMic.startRecording();
                playerCall.play();
                Log.i(TAG, "Started - earpiece mode");

                // Play AI response to STREAM_VOICE_CALL
                new Thread(() -> {
                    byte[] buf = new byte[4096];
                    try {
                        int r;
                        while (running && (r = in.read(buf)) > 0) {
                            playerCall.write(buf, 0, r);
                            Log.d(TAG, "Played " + r + " bytes to call stream");
                        }
                    } catch (Exception e) { Log.e(TAG, "Play: " + e.getMessage()); }
                }).start();

                // Send mic audio to MSI
                byte[] buf = new byte[bufSize];
                while (running) {
                    int r = recMic.read(buf, 0, buf.length);
                    if (r > 0) { out.write(buf, 0, r); out.flush(); }
                }
            } catch (Exception e) { Log.e(TAG, "Bridge: " + e.getMessage()); }
        }).start();
    }

    private void stopBridge() {
        running = false;
        try { if (recMic != null) { recMic.stop(); recMic.release(); } } catch (Exception ignored) {}
        try { if (playerCall != null) { playerCall.stop(); playerCall.release(); } } catch (Exception ignored) {}
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
        try {
            AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
            am.setMode(AudioManager.MODE_NORMAL);
        } catch (Exception ignored) {}
        Log.i(TAG, "Bridge stopped");
    }

    @Override public void onCallRemoved(Call call) { stopBridge(); }
}
