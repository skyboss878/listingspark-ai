import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL;

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('processing');

  useEffect(() => {
    const paymentId = searchParams.get('paymentId');
    const payerId = searchParams.get('PayerID');

    if (paymentId && payerId) {
      fetch(`${API_URL}/api/payment/execute-payment?paymentId=${paymentId}&PayerID=${payerId}`)
        .then(res => res.json())
        .then(data => {
          setStatus('success');
          console.log('Payment completed:', data);
        })
        .catch(err => {
          setStatus('error');
          console.error('Payment execution failed:', err);
        });
    }
  }, [searchParams]);

  return (
    <div className="payment-result">
      {status === 'processing' && <h1>Processing your payment...</h1>}
      {status === 'success' && (
        <>
          <h1>✓ Payment Successful!</h1>
          <p>Thank you for subscribing. Your account has been activated.</p>
        </>
      )}
      {status === 'error' && (
        <>
          <h1>Payment Failed</h1>
          <p>There was an issue processing your payment. Please try again.</p>
        </>
      )}
    </div>
  );
}
