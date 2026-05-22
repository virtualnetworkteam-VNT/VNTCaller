package com.vnt.caller;
import android.net.Uri;
import android.os.Bundle;
import android.telecom.*;
import android.util.Log;

public class VNTConnectionService extends ConnectionService {
    private static final String TAG = "VNTConnSvc";
    
    @Override
    public Connection onCreateIncomingConnection(PhoneAccountHandle handle, ConnectionRequest req) {
        Log.i(TAG, "Incoming connection: " + req.getAddress());
        VNTConnection conn = new VNTConnection(getApplicationContext());
        conn.setAddress(req.getAddress(), TelecomManager.PRESENTATION_ALLOWED);
        conn.setCallerDisplayName("VNT Caller", TelecomManager.PRESENTATION_ALLOWED);
        conn.setAudioModeIsVoip(true);
        conn.setInitializing();
        conn.setActive();
        // Route to AI bridge
        String caller = req.getAddress().getSchemeSpecificPart();
        conn.startAIBridge(caller);
        return conn;
    }

    @Override
    public Connection onCreateOutgoingConnection(PhoneAccountHandle handle, ConnectionRequest req) {
        Log.i(TAG, "Outgoing connection: " + req.getAddress());
        VNTConnection conn = new VNTConnection(getApplicationContext());
        conn.setAddress(req.getAddress(), TelecomManager.PRESENTATION_ALLOWED);
        conn.setAudioModeIsVoip(true);
        conn.setDialing();
        conn.setActive();
        String number = req.getAddress().getSchemeSpecificPart();
        conn.startAIBridge(number);
        return conn;
    }
}
