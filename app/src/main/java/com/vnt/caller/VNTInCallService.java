package com.vnt.caller;
import android.telecom.Call;
import android.telecom.InCallService;
import android.util.Log;

public class VNTInCallService extends InCallService {
    private static final String TAG = "VNTInCall";

    @Override
    public void onCallAdded(Call call) {
        Log.i(TAG, "Call added state: " + call.getState());
        // Auto-answer DISABLED - Alias audio bridge not functional on unrooted device
        // Phone rings normally, user answers manually
    }

    @Override
    public void onCallRemoved(Call call) {
        Log.i(TAG, "Call removed");
    }
}
