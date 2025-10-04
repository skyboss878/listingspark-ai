import { useState } from 'react';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';

const API_URL = import.meta.env.VITE_API_URL;

const pricingTiers = {
  starter: {
    name: "Starter",
    price: 29,
    features: [
      "5 Property Listings",
      "Basic Viral Content Generation",
      "Instagram & Facebook Content",
      "Email Support",
      "Basic Analytics"
    ]
  },
  professional: {
    name: "Professional",
    price: 79,
    features: [
      "Unlimited Property Listings",
      "Advanced AI Content Generation",
      "All Social Media Platforms",
      "Virtual Tour Creation",
      "Advanced Analytics",
      "Priority Support",
      "Custom Branding"
    ]
  },
  enterprise: {
    name: "Enterprise",
    price: 149,
    features: [
      "Everything in Professional",
      "Multi-Agent Team Access",
      "White-label Solution",
      "API Access",
      "Custom Integrations",
      "Dedicated Account Manager",
      "24/7 Phone Support"
    ]
  }
};

export default function Pricing() {
  const [selectedTier, setSelectedTier] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePayPalClick = async (tier) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/payment/create-payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tier: tier,
          return_url: `${window.location.origin}/payment/success`,
          cancel_url: `${window.location.origin}/payment/cancel`
        })
      });

      const data = await response.json();
      if (data.approval_url) {
        window.location.href = data.approval_url;
      }
    } catch (error) {
      console.error('Payment error:', error);
      alert('Payment failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pricing-container">
      <h1>Choose Your Plan</h1>
      <div className="pricing-grid">
        {Object.entries(pricingTiers).map(([key, tier]) => (
          <div key={key} className="pricing-card">
            <h2>{tier.name}</h2>
            <div className="price">
              <span className="currency">$</span>
              <span className="amount">{tier.price}</span>
              <span className="period">/month</span>
            </div>
            <ul className="features">
              {tier.features.map((feature, idx) => (
                <li key={idx}>✓ {feature}</li>
              ))}
            </ul>
            <button 
              onClick={() => handlePayPalClick(key)}
              disabled={loading}
              className="subscribe-btn"
            >
              {loading ? 'Processing...' : 'Subscribe Now'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
