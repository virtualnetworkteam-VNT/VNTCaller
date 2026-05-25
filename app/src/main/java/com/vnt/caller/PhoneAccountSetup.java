package com.vnt.caller;
import android.content.ComponentName;
import android.content.Context;
import android.net.Uri;
import android.os.Bundle;
import android.telecom.PhoneAccount;
import android.telecom.PhoneAccountHandle;
import android.telecom.TelecomManager;
import android.util.Log;

public class PhoneAccountSetup {
    private static final String TAG = "PhoneAccount";
    public static final String ACCOUNT_ID = "vnt_phone_account";

    public static PhoneAccountHandle getHandle(Context ctx) {
        ComponentName comp = new ComponentName(ctx, VNTConnectionService.class);
        return new PhoneAccountHandle(comp, ACCOUNT_ID);
    }

    public static void register(Context ctx) {
        try {
            TelecomManager tm = (TelecomManager) ctx.getSystemService(Context.TELECOM_SERVICE);
            PhoneAccountHandle handle = getHandle(ctx);
            PhoneAccount account = PhoneAccount.builder(handle, "VNT AI")
                .setCapabilities(
                    PhoneAccount.CAPABILITY_CALL_PROVIDER |
                    PhoneAccount.CAPABILITY_CONNECTION_MANAGER |
                    PhoneAccount.CAPABILITY_SUPPORTS_VIDEO_CALLING
                )
                .setSupportedUriSchemes(java.util.Arrays.asList("tel", "sip"))
                .build();
            tm.registerPhoneAccount(account);
            // Enable this account for calls
            tm.setUserSelectedOutgoingPhoneAccount(handle);
            Log.i(TAG, "Phone account registered and set as outgoing");
        } catch (Exception e) {
            Log.e(TAG, "Registration failed: " + e.getMessage());
        }
    }

    public static void makeCall(Context ctx, String number) {
        try {
            TelecomManager tm = (TelecomManager) ctx.getSystemService(Context.TELECOM_SERVICE);
            Bundle extras = new Bundle();
            extras.putParcelable(TelecomManager.EXTRA_PHONE_ACCOUNT_HANDLE, getHandle(ctx));
            tm.placeCall(Uri.fromParts("tel", number, null), extras);
            Log.i(TAG, "Call placed to " + number);
        } catch (Exception e) {
            Log.e(TAG, "makeCall failed: " + e.getMessage());
        }
    }
}
