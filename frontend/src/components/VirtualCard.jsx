import React, { useState } from "react";
import API_BASE_URL from "../api/config";

export default function VirtualCard({ card, onSimulateTap }) {
  const [loading, setLoading] = useState(false);
  const [provisioned, setProvisioned] = useState(false);

  const handleAddToAppleWallet = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/cards/wallet/provision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          card_id: card?.id || "card_momo_9921",
          target_wallet: "APPLE_PAY",
          device_id: "iphone_demo_device_001",
        }),
      });
      const data = await response.json();
      if (data.status === "READY_FOR_WALLET") {
        setProvisioned(true);
      }
    } catch (err) {
      console.error("Wallet provisioning error", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-yellow-400 to-amber-500 rounded-2xl p-6 text-black shadow-xl max-w-sm mx-auto">
      <div className="flex justify-between items-center mb-8">
        <span className="font-bold tracking-wider">MoMo SmartMoney</span>
        <span className="font-semibold text-xs bg-black text-white px-2 py-1 rounded">Virtual Mastercard</span>
      </div>

      <div className="text-xl tracking-widest font-mono mb-4">
        •••• •••• •••• {card?.last4 || "4288"}
      </div>

      <div className="flex justify-between text-xs mb-6">
        <div>
          <span className="block opacity-75">CARDHOLDER</span>
          <span className="font-bold">{card?.holder_name || "MTN MoMo User"}</span>
        </div>
        <div>
          <span className="block opacity-75">EXPIRES</span>
          <span className="font-bold">08/29</span>
        </div>
      </div>

      <div className="space-y-2">
        {!provisioned ? (
          <button
            onClick={handleAddToAppleWallet}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-black text-white font-medium py-2.5 rounded-xl hover:bg-neutral-800 transition shadow"
          >
            <svg className="w-5 h-5 fill-current" viewBox="0 0 170 170">
              <path d="M150.37 130.25c-2.45 5.66-5.35 10.87-8.71 15.66-4.58 6.53-8.33 11.05-11.22 13.56-4.48 4.12-9.28 6.23-14.42 6.35-3.69 0-8.14-1.05-13.32-3.18-5.19-2.12-9.97-3.17-14.34-3.17-4.58 0-9.49 1.05-14.75 3.17-5.26 2.13-9.5 3.24-12.74 3.35-4.35.13-9.16-1.9-14.42-6.08-3.69-3.04-7.69-7.85-12-14.44-6.19-9.45-11.05-20.3-14.58-32.55-3.53-12.25-5.3-24.1-5.3-35.55 0-14.12 3.63-25.9 10.89-35.34 7.26-9.44 16.35-14.28 27.27-14.51 4.79 0 10.35 1.28 16.68 3.84 6.33 2.56 10.15 3.84 11.46 3.84 1.1 0 5.09-1.39 11.97-4.17 6.88-2.78 12.57-3.95 17.07-3.51 12.82.78 22.82 5.67 30 14.67-11.25 6.83-16.76 16.29-16.53 28.38.23 9.44 3.86 17.38 10.89 23.82 7.03 6.44 15.53 10.14 25.5 11.1-2.22 6.67-4.87 13.43-7.95 20.28zM119.22 33.56c0-7.23 2.65-14.07 7.95-20.52 5.3-6.45 11.83-10.45 19.58-12-1.22 7.55-4.08 14.32-8.58 20.31-4.5 5.99-10.8 9.94-18.95 11.86v.35z"/>
            </svg>
            {loading ? "Adding to Wallet..." : "Add to Apple Wallet"}
          </button>
        ) : (
          <div className="text-center text-xs font-semibold text-black bg-white/70 py-2 rounded-xl">
            ✓ Added to Apple Wallet (Ready for POS Tap)
          </div>
        )}

        <button
          onClick={onSimulateTap}
          className="w-full text-xs font-semibold py-2 bg-yellow-600 text-white rounded-xl hover:bg-yellow-700 transition"
        >
          Simulate POS Contactless Tap
        </button>
      </div>
    </div>
  );
}
