package com.vnt.caller;
import android.telecom.Call;
import android.telecom.InCallService;
import android.util.Log;

public class VNTInCallService extends InCallService {
    private static final String TAG = "VNTInCall";
    
    @Override
    public void onCallAdded(Call call) {
        Log.i(TAG, "Call added: " + call.getState());
        // Auto-answer incoming calls
        if (call.getState() == Call.STATE_RINGING) {
            call.answer(0);
        }
    }
    
    @Override
    public void onCallRemoved(Call call) {
        Log.i(TAG, "Call removed");
    }
}
