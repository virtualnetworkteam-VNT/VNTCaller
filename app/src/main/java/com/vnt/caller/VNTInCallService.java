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
        if (bridgeRunning) return;
        bridgeRunning = true;
        String caller = "";
        try { caller = call.getDetails().getHandle().getSchemeSpecificPart(); } catch (Exception ignored) {}
        final String callerNum = caller;

        // Enable speakerphone so Alias voice goes through mic back to caller
        AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
        am.setMode(AudioManager.MODE_IN_CALL);
        am.setSpeakerphoneOn(true);
        Log.i(TAG, "Speakerphone ON - bridge starting for: " + callerNum);

        new Thread(() -> {
            try {
                socket = new Socket(BRIDGE_HOST, BRIDGE_PORT);
                OutputStream out = socket.getOutputStream();
                InputStream in = socket.getInputStream();
                out.write((callerNum + "\n").getBytes());
                out.flush();

                int bufSize = AudioRecord.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2;

                // Capture mic audio (picks up caller voice via speakerphone)
                recorder = new AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION,
                    SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT, bufSize);

                // Play Alias response through speaker loudly
                // Speakerphone carries it back through mic to S25
                int playBuf = AudioTrack.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2;
                player = new AudioTrack.Builder()
                    .setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build())
                    .setAudioFormat(new AudioFormat.Builder()
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(SAMPLE_RATE)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                        .build())
                    .setBufferSizeInBytes(playBuf)
                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .build();

                recorder.startRecording();
                player.play();
                Log.i(TAG, "Recording + playback started");

                // Play AI responses through speaker
                new Thread(() -> {
                    byte[] buf = new byte[4096];
                    try {
                        int r;
                        while (bridgeRunning && (r = in.read(buf)) > 0) {
                            player.write(buf, 0, r);
                        }
                    } catch (Exception e) { Log.e(TAG, "Playback: " + e.getMessage()); }
                }).start();

                // Stream mic to AI
                byte[] buf = new byte[bufSize];
                while (bridgeRunning) {
                    int r = recorder.read(buf, 0, buf.length);
                    if (r > 0) { out.write(buf, 0, r); out.flush(); }
                }
            } catch (Exception e) {
                Log.e(TAG, "Bridge error: " + e.getMessage());
            }
        }).start();
    }

    private void stopBridge() {
        bridgeRunning = false;
        try { if (recorder != null) { recorder.stop(); recorder.release(); } } catch (Exception ignored) {}
        try { if (player != null) { player.stop(); player.release(); } } catch (Exception ignored) {}
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
        try {
            AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
            am.setSpeakerphoneOn(false);
            am.setMode(AudioManager.MODE_NORMAL);
        } catch (Exception ignored) {}
    }

    @Override
    public void onCallRemoved(Call call) { stopBridge(); }
}
