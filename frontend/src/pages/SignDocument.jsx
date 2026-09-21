import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import api from '../api';
import { getErrorMessage } from '../utils/errorHelpers';

const SignDocument = () => {
  const { documentId } = useParams();
  const canvasRef = useRef(null);
  const drawingRef = useRef(false);
  const lastPointRef = useRef(null);

  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [hasSignature, setHasSignature] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [signed, setSigned] = useState(false);

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        const response = await api.get(`/documents/${documentId}/public`);
        setDocument(response.data);
        if (response.data.status === 'signed') {
          setSigned(true);
        }
      } catch (error) {
        setLoadError(getErrorMessage(error, 'This document could not be found or is no longer available.'));
      } finally {
        setLoading(false);
      }
    };
    fetchDocument();
  }, [documentId]);

  const getCanvasPoint = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return {
      x: (clientX - rect.left) * (canvas.width / rect.width),
      y: (clientY - rect.top) * (canvas.height / rect.height),
    };
  };

  const startDrawing = (e) => {
    e.preventDefault();
    drawingRef.current = true;
    lastPointRef.current = getCanvasPoint(e);
  };

  const draw = (e) => {
    if (!drawingRef.current) return;
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const point = getCanvasPoint(e);

    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();
    ctx.moveTo(lastPointRef.current.x, lastPointRef.current.y);
    ctx.lineTo(point.x, point.y);
    ctx.stroke();

    lastPointRef.current = point;
    setHasSignature(true);
  };

  const stopDrawing = () => {
    drawingRef.current = false;
  };

  const clearSignature = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.width = canvas.offsetWidth * 2;
      canvas.height = canvas.offsetHeight * 2;
      const ctx = canvas.getContext('2d');
      ctx.scale(2, 2);
    }
  }, [document]);

  const handleSubmit = async () => {
    if (!hasSignature) {
      toast.error('Please draw your signature first');
      return;
    }

    setSubmitting(true);
    try {
      const signatureData = canvasRef.current.toDataURL('image/png');
      await api.post(`/documents/${documentId}/sign`, {
        document_id: documentId,
        signature_data: signatureData,
        signed_at: new Date().toISOString(),
      });
      setSigned(true);
      toast.success('Document signed successfully!');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to submit signature. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p>Loading document...</p>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white p-6">
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20 max-w-md text-center">
          <div className="text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold mb-2">Document Not Found</h2>
          <p className="text-purple-200">{loadError}</p>
        </div>
      </div>
    );
  }

  if (signed) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20 max-w-md text-center"
        >
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold mb-2">Signed Successfully</h2>
          <p className="text-purple-200">
            Thank you for signing <strong>{document?.title}</strong>. A copy has been recorded.
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white p-4 sm:p-6">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold">📝 Review &amp; Sign</h1>
          <p className="text-purple-200 text-sm mt-1">{document?.title}</p>
        </div>

        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 mb-6 max-h-96 overflow-y-auto">
          <pre className="whitespace-pre-wrap font-sans text-sm text-purple-50 leading-relaxed">
            {document?.content}
          </pre>
        </div>

        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 mb-6">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold text-sm">Draw your signature below</h3>
            <button
              onClick={clearSignature}
              className="text-xs text-purple-300 hover:text-white transition-colors"
            >
              Clear
            </button>
          </div>
          <canvas
            ref={canvasRef}
            className="w-full h-40 bg-white rounded-lg touch-none"
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
            onTouchStart={startDrawing}
            onTouchMove={draw}
            onTouchEnd={stopDrawing}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={submitting || !hasSignature}
          className="w-full bg-gradient-to-r from-purple-600 to-pink-600 px-8 py-4 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? 'Submitting...' : 'Submit Signature'}
        </button>
      </div>
    </div>
  );
};

export default SignDocument;
