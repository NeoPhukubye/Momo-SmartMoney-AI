import React, { useEffect, useRef, useState } from 'react';

export default function GooglePayCheckout({ amount = '50.00', onPaymentSuccess }) {
  const containerRef = useRef(null);
  const [paymentsClient, setPaymentsClient] = useState(null);

  const baseRequest = {
    apiVersion: 2,
    apiVersionMinor: 0,
  };

  const allowedCardNetworks = ['MASTERCARD', 'VISA'];
  const allowedCardAuthMethods = ['PAN_ONLY', 'CRYPTOGRAM_3DS'];

  const baseCardPaymentMethod = {
    type: 'CARD',
    parameters: {
      allowedAuthMethods: allowedCardAuthMethods,
      allowedCardNetworks: allowedCardNetworks,
    },
  };

  const cardPaymentMethod = {
    ...baseCardPaymentMethod,
    tokenizationSpecification: {
      type: 'PAYMENT_GATEWAY',
      parameters: {
        gateway: 'example',
        gatewayMerchantId: 'momoSmartMoneyGateway',
      },
    },
  };

  useEffect(() => {
    if (!window.google?.payments?.api) return;

    const client = new window.google.payments.api.PaymentsClient({
      environment: 'TEST', // Set to 'TEST' to allow checkout verification without production merchant approval
    });
    setPaymentsClient(client);

    const isReadyToPayRequest = {
      ...baseRequest,
      allowedPaymentMethods: [baseCardPaymentMethod],
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
            onClick: onGooglePaymentButtonClicked,
          });
          containerRef.current.appendChild(button);
        }
      })
      .catch((err) => console.error('Google Pay isReadyToPay error:', err));
  }, []);

  const onGooglePaymentButtonClicked = () => {
    if (!paymentsClient) return;

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

    paymentsClient
      .loadPaymentData(paymentDataRequest)
      .then((paymentData) => {
        if (onPaymentSuccess) {
          onPaymentSuccess(paymentData);
        }
      })
      .catch((err) => {
        // Canceled or dismissed by user
        console.warn('Payment flow closed or errored:', err);
      });
  };

  return (
    <div className="w-full flex justify-center my-2">
      <div ref={containerRef} className="w-full max-w-xs h-11" />
    </div>
  );
}
