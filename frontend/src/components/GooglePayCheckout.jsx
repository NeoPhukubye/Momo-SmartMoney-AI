import React, { useState } from "react";
import GooglePayButton from "@google-pay/button-react";

export default function GooglePayCheckout({ amount = 150.0, onSuccess }) {
  const [paymentStatus, setPaymentStatus] = useState(null);

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-neutral-200">
      <h3 className="font-semibold text-neutral-900 mb-2">MoMo Wallet Fast Pay</h3>
      <p className="text-sm text-neutral-500 mb-4">
        Pay securely using Google Pay. All payments are screened by Scam Shield in real time.
      </p>

      <div className="flex justify-between items-center py-2 border-b border-neutral-100 mb-4 text-sm font-medium">
        <span>Total Due</span>
        <span className="text-lg font-bold text-neutral-900">R{amount.toFixed(2)}</span>
      </div>

      <div className="flex justify-center">
        <GooglePayButton
          environment="TEST"
          buttonColor="black"
          buttonType="pay"
          paymentRequest={{
            apiVersion: 2,
            apiVersionMinor: 0,
            allowedPaymentMethods: [
              {
                type: "CARD",
                parameters: {
                  allowedAuthMethods: ["PAN_ONLY", "CRYPTOGRAM_3DS"],
                  allowedCardNetworks: ["MASTERCARD", "VISA"],
                },
                tokenizationSpecification: {
                  type: "PAYMENT_GATEWAY",
                  parameters: {
                    gateway: "example",
                    gatewayMerchantId: "exampleGatewayMerchantId",
                  },
                },
              },
            ],
            merchantInfo: {
              merchantId: "12345678901234567890",
              merchantName: "MoMo SmartMoney AI",
            },
            transactionInfo: {
              totalPriceStatus: "FINAL",
              totalPriceLabel: "Total",
              totalPrice: amount.toFixed(2),
              currencyCode: "ZAR",
              countryCode: "ZA",
            },
          }}
          onLoadPaymentData={async (paymentData) => {
            try {
              const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/cards/tap/authorize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  user_id: "demo_user_01",
                  merchant_name: "Google Pay Checkout",
                  merchant_id: "GPAY_CHECKOUT_TERMINAL",
                  amount: amount,
                  channel: "GOOGLE_PAY_WEB",
                }),
              });
              const result = await res.json();
              if (result.decision === "APPROVED") {
                setPaymentStatus("Payment Authorized via Google Pay!");
                if (onSuccess) onSuccess(result);
              } else {
                setPaymentStatus(`Declined: ${result.reason}`);
              }
            } catch (err) {
              setPaymentStatus("Transaction processing failed.");
            }
          }}
        />
      </div>

      {paymentStatus && (
        <div className="mt-4 p-3 bg-neutral-50 rounded-lg text-xs font-semibold text-center text-neutral-800">
          {paymentStatus}
        </div>
      )}
    </div>
  );
}
