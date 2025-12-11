import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Clock, CreditCard } from 'lucide-react';
import api from '../api';

const TrialBanner = () => {
  const [trialInfo, setTrialInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    checkTrialStatus();
  }, []);

  const checkTrialStatus = async () => {
    try {
      console.log('TrialBanner: Checking trial status...');
      const response = await api.get('/auth/trial-info');
      console.log('TrialBanner: API response:', response.data);
      setTrialInfo(response.data);
      setLoading(false);

      // If trial expired, show upgrade prompt
      if (response.data.trial_expired && response.data.needs_subscription) {
        // Optionally redirect to pricing after a delay
        // setTimeout(() => navigate('/pricing'), 3000);
      }
    } catch (error) {
      console.error('TrialBanner: Error checking trial:', error);
      setLoading(false);
    }
  };

  console.log('TrialBanner: Render check - loading:', loading, 'trialInfo:', trialInfo);
  
  if (loading || !trialInfo) {
    console.log('TrialBanner: Returning null - loading:', loading, 'trialInfo:', !!trialInfo);
    return null;
  }

  // Trial expired - must subscribe
  if (trialInfo.trial_expired && trialInfo.needs_subscription) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-red-500" />
            <div>
              <h3 className="text-lg font-semibold text-red-900">
                Free Trial Ended
              </h3>
              <p className="text-red-700">
                Your 3-day free trial has expired. Subscribe now to continue using Real360 AI.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/pricing')}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold flex items-center gap-2"
          >
            <CreditCard className="w-5 h-5" />
            Subscribe Now
          </button>
        </div>
      </div>
    );
  }

  // Trial active - show remaining time
  if (trialInfo.trial_active) {
    const isLastDay = trialInfo.days_remaining <= 1;
    const bgColor = isLastDay ? 'bg-yellow-50' : 'bg-blue-50';
    const borderColor = isLastDay ? 'border-yellow-500' : 'border-blue-500';
    const textColor = isLastDay ? 'text-yellow-900' : 'text-blue-900';
    const accentColor = isLastDay ? 'text-yellow-500' : 'text-blue-500';

    return (
      <div className={`${bgColor} border-l-4 ${borderColor} p-4 mb-6`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock className={`w-6 h-6 ${accentColor}`} />
            <div>
              <h3 className={`text-lg font-semibold ${textColor}`}>
                Free Trial Active
              </h3>
              <p className={textColor}>
                {trialInfo.days_remaining === 0 
                  ? `${trialInfo.hours_remaining} hours remaining`
                  : `${trialInfo.days_remaining} day${trialInfo.days_remaining > 1 ? 's' : ''} remaining`
                } in your free trial
              </p>
            </div>
          </div>
          {trialInfo.show_upgrade_prompt && (
            <button
              onClick={() => navigate('/pricing')}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 font-semibold"
            >
              Upgrade Now
            </button>
          )}
        </div>
      </div>
    );
  }

  // Subscribed - show success
  if (trialInfo.subscribed) {
    return (
      <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-6">
        <div className="flex items-center gap-3">
          <CreditCard className="w-6 h-6 text-green-500" />
          <div>
            <h3 className="text-lg font-semibold text-green-900">
              Active Subscription
            </h3>
            <p className="text-green-700">
              You have full access to all Real360 AI features
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default TrialBanner;
