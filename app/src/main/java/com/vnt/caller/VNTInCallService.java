package com.vnt.caller;
import android.os.Handler;
import android.telecom.Call;
import android.telecom.InCallService;
import android.util.Log;

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
            }
        });
        if (call.getState() == Call.STATE_RINGING) {
            answerCall(call);
        } else {
            new Handler().postDelayed(() -> {
                if (call.getState() == Call.STATE_RINGING) answerCall(call);
            }, 1000);
        }
    }

    private void answerCall(Call call) {
        try {
            Log.i(TAG, "Auto-answering");
            call.answer(0);
        } catch (Exception e) {
            Log.e(TAG, "Answer failed: " + e.getMessage());
        }
    }

    @Override
    public void onCallRemoved(Call call) {
        Log.i(TAG, "Call removed");
    }
}
