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
    private AudioRecord recorder;
    private AudioTrack player;
    private WebSocketClient wsClient;
    private boolean running = false;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        createNotification();
        if (intent != null && intent.hasExtra("room")) {
            startCall(intent.getStringExtra("room"), intent.getStringExtra("number"));
        }
        return START_STICKY;
    }

    private void createNotification() {
        NotificationChannel ch = new NotificationChannel("vnt","VNT Caller",NotificationManager.IMPORTANCE_LOW);
        getSystemService(NotificationManager.class).createNotificationChannel(ch);
        startForeground(1, new NotificationCompat.Builder(this,"vnt")
            .setContentTitle("VNT Caller").setContentText("AI answering active")
            .setSmallIcon(android.R.drawable.ic_menu_call).build());
    }

    private void startCall(String room, String number) {
        new Thread(() -> {
            try {
                String url = WS_URL + "/" + room + "?caller=" + (number != null ? number.replace("+","") : "unknown");
                wsClient = new WebSocketClient(new URI(url)) {
                    @Override public void onOpen(ServerHandshake h) { startCapture(); }
                    @Override public void onMessage(ByteBuffer buf) { playAudio(buf.array()); }
                    @Override public void onMessage(String msg) {}
                    @Override public void onClose(int c, String r, boolean remote) { stopCapture(); }
                    @Override public void onError(Exception e) { Log.e(TAG, e.getMessage()); }
                };
                wsClient.connect();
            } catch (Exception e) { Log.e(TAG, "startCall: " + e.getMessage()); }
        }).start();
    }

    private void startCapture() {
        int buf = AudioRecord.getMinBufferSize(16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        recorder = new AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION,
            16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, buf);
        player = new AudioTrack.Builder()
            .setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setAudioFormat(new AudioFormat.Builder()
                .setSampleRate(48000).setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
            .setBufferSizeInBytes(buf*4).setTransferMode(AudioTrack.MODE_STREAM).build();
        player.play(); recorder.startRecording(); running = true;
        byte[] data = new byte[buf];
        while (running) {
            int read = recorder.read(data, 0, data.length);
            if (read > 0 && wsClient != null && wsClient.isOpen())
                wsClient.send(ByteBuffer.wrap(data, 0, read));
        }
    }

    private void playAudio(byte[] data) { if (player != null) player.write(data, 0, data.length); }
    private void stopCapture() { running = false; if(recorder!=null){recorder.stop();recorder.release();} if(player!=null){player.stop();player.release();} }
    @Override public IBinder onBind(Intent i) { return null; }
    @Override public void onDestroy() { stopCapture(); if(wsClient!=null) wsClient.close(); }
}
