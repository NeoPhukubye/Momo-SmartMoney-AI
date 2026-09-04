import React, { useEffect, useRef } from 'react';

export default function GooglePayCheckout({ amount = '50.00', onPaymentSuccess }) {
  const containerRef = useRef(null);

  useEffect(() => {
    // Only proceed if window.google and payments api are truly available
    if (typeof window === 'undefined' || !window.google?.payments?.api) {
      return;
    }

    try {
      const client = new window.google.payments.api.PaymentsClient({
        environment: 'TEST', // Set to 'TEST' to allow checkout verification without production merchant approval
      });

      const baseRequest = {
        apiVersion: 2,
        apiVersionMinor: 0,
      };

      const isReadyToPayRequest = {
        ...baseRequest,
        allowedPaymentMethods: [
          {
            type: 'CARD',
            parameters: {
              allowedAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
              allowedCardNetworks: ['MASTERCARD', 'VISA'],
            },
          },
        ],
      };

      client
        .isReadyToPay(isReadyToPayRequest)
        .then((response) => {
          if (response.result && containerRef.current) {
            containerRef.current.innerHTML = '';
            const button = client.createButton({
              buttonColor: 'black',
              buttonType: 'pay',
              buttonSizeMode: 'fill',
              onClick: () => {
                const cardPaymentMethod = {
                  type: 'CARD',
                  parameters: {
                    allowedAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
                    allowedCardNetworks: ['MASTERCARD', 'VISA'],
                  },
                  tokenizationSpecification: {
                    type: 'PAYMENT_GATEWAY',
                    parameters: {
                      gateway: 'example',
                      gatewayMerchantId: 'momoSmartMoneyGateway',
                    },
                  },
                };

                const paymentDataRequest = {
                  ...baseRequest,
                  allowedPaymentMethods: [cardPaymentMethod],
                  transactionInfo: {
                    totalPriceStatus: 'FINAL',
                    totalPrice: String(amount),
                    currencyCode: 'ZAR',
                    countryCode: 'ZA',
                  },
                  merchantInfo: {
                    merchantName: 'MoMo SmartMoney AI',
                  },
                };

                client
                  .loadPaymentData(paymentDataRequest)
                  .then((paymentData) => {
                    if (onPaymentSuccess) onPaymentSuccess(paymentData);
                  })
                  .catch((err) => console.warn('Payment flow closed or errored:', err));
              },
            });
            containerRef.current.appendChild(button);
          }
        })
        .catch((err) => console.error('Google Pay isReadyToPay error:', err));
    } catch (e) {
      console.warn('Google Pay init suppressed:', e);
    }
  }, [amount, onPaymentSuccess]);

  return (
    <div className="w-full flex justify-center my-2">
      <div ref={containerRef} className="w-full max-w-xs h-11" />
    </div>
  );
}
