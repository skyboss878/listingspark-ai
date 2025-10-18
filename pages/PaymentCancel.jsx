import { useNavigate } from 'react-router-dom';

export default function PaymentCancel() {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom right, #6b21a8, #1e3a8a, #4c1d95)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        borderRadius: '16px',
        padding: '40px',
        maxWidth: '500px',
        width: '100%',
        textAlign: 'center',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        color: 'white'
      }}>
        <div style={{ fontSize: '80px', marginBottom: '24px' }}>😔</div>
        
        <h1 style={{ 
          fontSize: '32px', 
          marginBottom: '16px', 
          fontWeight: 'bold'
        }}>
          Payment Cancelled
        </h1>
        
        <p style={{ 
          fontSize: '18px', 
          opacity: 0.9, 
          marginBottom: '32px',
          lineHeight: '1.6'
        }}>
          No worries! You can subscribe anytime to unlock all the powerful features of ListingSpark Pro.
        </p>

        <div style={{
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          border: '1px solid rgba(59, 130, 246, 0.5)',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '32px',
          textAlign: 'left'
        }}>
          <p style={{ fontSize: '16px', margin: '0 0 12px 0', fontWeight: 'bold' }}>
            What you're missing:
          </p>
          <ul style={{ fontSize: '14px', margin: 0, paddingLeft: '20px', opacity: 0.9 }}>
            <li>AI-Powered Content Generation</li>
            <li>360° Virtual Tours</li>
            <li>Unlimited Property Listings</li>
            <li>Social Media Marketing Tools</li>
            <li>Advanced Analytics</li>
          </ul>
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => navigate('/pricing')}
            style={{
              background: 'linear-gradient(to right, #a855f7, #ec4899)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '14px 28px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'transform 0.2s',
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            View Plans Again
          </button>
          
          <button
            onClick={() => navigate('/')}
            style={{
              background: 'transparent',
              color: 'white',
              border: '2px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '8px',
              padding: '14px 28px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
              e.target.style.borderColor = 'rgba(255, 255, 255, 0.5)';
            }}
            onMouseOut={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.borderColor = 'rgba(255, 255, 255, 0.3)';
            }}
          >
            Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}
