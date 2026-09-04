import React, { useState } from 'react';

export default function GoogleWalletProvisionButton({ cardId }) {
  const [loading, setLoading] = useState(false);
  const [isAdded, setIsAdded] = useState(false);

  const handleAddCard = async () => {
    setLoading(true);
    // Simulate card tokenization delay (Mastercard MDES / Google Wallet TSP)
    setTimeout(() => {
      setLoading(false);
      setIsAdded(true);
    }, 1200);
  };

  return (
    <div className="w-full mt-2">
      {!isAdded ? (
        <button
          onClick={handleAddCard}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-black hover:bg-neutral-800 text-white font-medium py-3 px-4 rounded-xl transition shadow"
        >
          <img
            src="https://www.gstatic.com/instantbuy/svg/dark_gpay.svg"
            alt="Google Pay"
            className="h-5"
          />
          <span className="text-sm font-semibold">
            {loading ? "Tokenizing Card..." : "Add to Google Wallet"}
          </span>
        </button>
      ) : (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 text-center">
          <div className="flex items-center justify-center gap-2 text-emerald-400 font-semibold text-sm mb-1">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
            </svg>
            Active in Google Wallet
          </div>
          <p className="text-xs text-neutral-300">
            DPAN •••• 4288 | Tap-to-Pay Ready on POS Terminals
          </p>
        </div>
      )}
    </div>
  );
}
