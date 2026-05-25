package com.vnt.caller;
import android.net.Uri;
import android.telecom.*;
import android.util.Log;

public class VNTConnectionService extends ConnectionService {
    private static final String TAG = "VNTConnSvc";

    @Override
    public Connection onCreateIncomingConnection(PhoneAccountHandle handle, ConnectionRequest req) {
        Log.i(TAG, "Incoming: " + req.getAddress());
        VNTConnection conn = new VNTConnection(getApplicationContext());
        conn.setAddress(req.getAddress(), TelecomManager.PRESENTATION_ALLOWED);
        conn.setCallerDisplayName("VNT", TelecomManager.PRESENTATION_ALLOWED);
        conn.setAudioModeIsVoip(true);
        conn.setActive();
        conn.startAIBridge(req.getAddress().getSchemeSpecificPart());
        return conn;
    }

    @Override
    public Connection onCreateOutgoingConnection(PhoneAccountHandle handle, ConnectionRequest req) {
        Log.i(TAG, "Outgoing: " + req.getAddress());
        VNTConnection conn = new VNTConnection(getApplicationContext());
        conn.setAddress(req.getAddress(), TelecomManager.PRESENTATION_ALLOWED);
        conn.setAudioModeIsVoip(true);
        conn.setDialing();
        conn.setActive();
        conn.startAIBridge(req.getAddress().getSchemeSpecificPart());
        return conn;
    }

    @Override
    public Connection onCreateIncomingConnectionFailed(PhoneAccountHandle h, ConnectionRequest r) {
        Log.e(TAG, "Incoming connection failed");
        return null;
    }

    @Override
    public Connection onCreateOutgoingConnectionFailed(PhoneAccountHandle h, ConnectionRequest r) {
        Log.e(TAG, "Outgoing connection failed");
        return null;
    }
}
