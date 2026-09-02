import React, { useState } from "react";
import API_BASE_URL from "../api/config";

export default function GoogleWalletProvisionButton({ cardId }) {
  const [provisioning, setProvisioning] = useState(false);
  const [added, setAdded] = useState(false);

  const handleAddToGoogleWallet = async () => {
    setProvisioning(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/cards/wallet/provision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          card_id: cardId || "card_momo_9921",
          target_wallet: "GOOGLE_PAY",
          device_id: "android_pixel_demo_device",
        }),
      });
      const data = await response.json();
      if (data.status === "READY_FOR_WALLET") {
        setAdded(true);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setProvisioning(false);
    }
  };

  return (
    <div>
      {!added ? (
        <button
          onClick={handleAddToGoogleWallet}
          disabled={provisioning}
          className="w-full flex items-center justify-center gap-2 bg-neutral-900 text-white font-medium py-2.5 px-4 rounded-xl hover:bg-black transition shadow-sm text-sm"
        >
          <img
            src="https://www.gstatic.com/instantbuy/svg/dark_gpay.svg"
            alt="Google Pay"
            className="h-5"
          />
          <span>{provisioning ? "Connecting Google Wallet..." : "Add to Google Wallet"}</span>
        </button>
      ) : (
        <div className="text-center text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 py-2 rounded-xl">
          ✓ Active in Google Wallet (Ready for Contactless POS Tap)
        </div>
      )}
    </div>
  );
}
