package com.vnt.caller;
import android.content.Intent;
import android.telecom.Call;
import android.telecom.InCallService;
import android.util.Log;
import android.os.Handler;
import android.os.Looper;

public class VNTInCallService extends InCallService {
    private static final String TAG = "VNTInCall";

    @Override
    public void onCallAdded(Call call) {
        Log.i(TAG, "Call added state: " + call.getState());
        call.registerCallback(new Call.Callback() {
            @Override
            public void onStateChanged(Call c, int state) {
                Log.i(TAG, "State: " + state);
                if (state == Call.STATE_RINGING) answerCall(c);
                if (state == Call.STATE_ACTIVE) notifyBridge(c);
                if (state == Call.STATE_DISCONNECTED) stopBridge();
            }
        });
        if (call.getState() == Call.STATE_RINGING) answerCall(call);
        if (call.getState() == Call.STATE_ACTIVE) notifyBridge(call);
    }

    private void answerCall(Call call) {
        try { call.answer(0); Log.i(TAG, "Call answered"); }
        catch (Exception e) { Log.e(TAG, "Answer failed: " + e.getMessage()); }
    }

    private void notifyBridge(Call call) {
        String caller = "";
        try { caller = call.getDetails().getHandle().getSchemeSpecificPart(); } catch (Exception ignored) {}
        Log.i(TAG, "Call active, notifying bridge for: " + caller);
        // Notify MSI call bridge via TCP that call is active
        final String callerNum = caller;
        new Thread(() -> {
            try {
                java.net.Socket s = new java.net.Socket("192.168.10.96", 9998);
                String body = "{\"to\":\"" + callerNum + "\",\"action\":\"active\"}";
                String req = "POST /call HTTP/1.1\r\nContent-Length: " + body.length() + "\r\n\r\n" + body;
                s.getOutputStream().write(req.getBytes());
                s.getOutputStream().flush();
                s.close();
                Log.i(TAG, "Bridge notified");
            } catch (Exception e) { Log.e(TAG, "Bridge notify: " + e.getMessage()); }
        }).start();
    }

    private void stopBridge() {
        Log.i(TAG, "Call ended");
    }

    @Override
    public void onCallRemoved(Call call) { stopBridge(); }
}
