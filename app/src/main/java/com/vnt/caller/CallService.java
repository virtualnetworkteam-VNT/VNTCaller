package com.vnt.caller;
import android.app.*;
import android.content.*;
import android.media.*;
import android.os.*;
import android.util.Log;
import androidx.core.app.NotificationCompat;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import java.net.URI;
import java.nio.ByteBuffer;

public class CallService extends Service {
    private static final String TAG = "VNTCaller";
    private static final String WS_URL = "ws://192.168.10.96:9999";
    private static final String RYAN_NUMBER = "966568116899";
    private AudioRecord recorder;
    private AudioTrack player;
    private WebSocketClient wsClient;
    private boolean running = false;
    private String currentRoom = "vnt-general";

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && intent.hasExtra("room")) {
            currentRoom = intent.getStringExtra("room");
            String number = intent.getStringExtra("number");
            Log.i(TAG, "Call from " + number + " -> room: " + currentRoom);
            startCall();
        }
        createNotification();
        return START_STICKY;
    }

    private void createNotification() {
        NotificationChannel ch = new NotificationChannel("vnt", "VNT Caller", 
            NotificationManager.IMPORTANCE_LOW);
        getSystemService(NotificationManager.class).createNotificationChannel(ch);
        Notification n = new NotificationCompat.Builder(this, "vnt")
            .setContentTitle("VNT Caller Active")
            .setContentText("Alias & Mia ready")
            .setSmallIcon(android.R.drawable.ic_menu_call)
            .build();
        startForeground(1, n);
    }

    private void startCall() {
        new Thread(() -> {
            try {
                wsClient = new WebSocketClient(new URI(WS_URL + "/" + currentRoom)) {
                    @Override public void onOpen(ServerHandshake h) {
                        Log.i(TAG, "WS connected to " + currentRoom);
                        startAudioCapture();
                    }
                    @Override public void onMessage(ByteBuffer buf) {
                        playAudio(buf.array());
                    }
                    @Override public void onMessage(String msg) {}
                    @Override public void onClose(int c, String r, boolean remote) {
                        stopAudioCapture();
                    }
                    @Override public void onError(Exception e) {
                        Log.e(TAG, "WS error: " + e.getMessage());
                    }
                };
                wsClient.connect();
            } catch (Exception e) {
                Log.e(TAG, "Call error: " + e.getMessage());
            }
        }).start();
    }

    private void startAudioCapture() {
        int bufSize = AudioRecord.getMinBufferSize(16000,
            AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        recorder = new AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION,
            16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufSize);
        player = new AudioTrack.Builder()
            .setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setAudioFormat(new AudioFormat.Builder()
                .setSampleRate(48000).setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
            .setBufferSizeInBytes(bufSize * 4)
            .setTransferMode(AudioTrack.MODE_STREAM).build();
        player.play();
        recorder.startRecording();
        running = true;
        byte[] buf = new byte[bufSize];
        while (running) {
            int read = recorder.read(buf, 0, buf.length);
            if (read > 0 && wsClient != null && wsClient.isOpen()) {
                wsClient.send(ByteBuffer.wrap(buf, 0, read));
            }
        }
    }

    private void playAudio(byte[] data) {
        if (player != null) player.write(data, 0, data.length);
    }

    private void stopAudioCapture() {
        running = false;
        if (recorder != null) { recorder.stop(); recorder.release(); }
        if (player != null) { player.stop(); player.release(); }
    }

    @Override public IBinder onBind(Intent i) { return null; }
    @Override public void onDestroy() { stopAudioCapture(); if (wsClient != null) wsClient.close(); }
}
