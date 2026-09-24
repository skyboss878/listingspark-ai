import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import api from '../api';
import { getErrorMessage } from '../utils/errorHelpers';

const DOCUMENT_TYPES = [
  { value: 'listing_agreement', label: 'Listing Agreement' },
  { value: 'buyer_agreement', label: 'Buyer Agreement' },
  { value: 'purchase_agreement', label: 'Purchase Agreement' },
  { value: 'disclosure', label: 'Disclosure' },
  { value: 'addendum', label: 'Addendum' },
  { value: 'inspection', label: 'Inspection' },
  { value: 'escrow', label: 'Escrow' },
  { value: 'other', label: 'Other' },
];

const Clients = () => {
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddClient, setShowAddClient] = useState(false);
  const [savingClient, setSavingClient] = useState(false);
  const [expandedClientId, setExpandedClientId] = useState(null);
  const [clientDetail, setClientDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [showNewDoc, setShowNewDoc] = useState(false);
  const [savingDoc, setSavingDoc] = useState(false);
  const [sendingDocId, setSendingDocId] = useState(null);

  const [clientForm, setClientForm] = useState({
    first_name: '', last_name: '', email: '', phone: '', client_type: 'buyer',
  });

  const [docForm, setDocForm] = useState({
    document_type: 'buyer_agreement', title: '', content: '',
  });

  const fetchClients = useCallback(async () => {
    try {
      const response = await api.get('/clients');
      setClients(response.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to load clients'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  const handleClientFormChange = (e) => {
    const { name, value } = e.target;
    setClientForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleAddClient = async (e) => {
    e.preventDefault();
    setSavingClient(true);
    try {
      await api.post('/clients', clientForm);
      toast.success('Client added!');
      setClientForm({ first_name: '', last_name: '', email: '', phone: '', client_type: 'buyer' });
      setShowAddClient(false);
      fetchClients();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to add client'));
    } finally {
      setSavingClient(false);
    }
  };

  const toggleClient = async (clientId) => {
    if (expandedClientId === clientId) {
      setExpandedClientId(null);
      setClientDetail(null);
      setShowNewDoc(false);
      return;
    }
    setExpandedClientId(clientId);
    setShowNewDoc(false);
    setLoadingDetail(true);
    try {
      const response = await api.get(`/clients/${clientId}`);
      setClientDetail(response.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to load client details'));
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDocFormChange = (e) => {
    const { name, value } = e.target;
    setDocForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateDocument = async (e) => {
    e.preventDefault();
    if (!docForm.title || !docForm.content) {
      toast.error('Title and content are required');
      return;
    }
    setSavingDoc(true);
    try {
      await api.post('/documents', { ...docForm, client_id: expandedClientId });
      toast.success('Document created!');
      setDocForm({ document_type: 'buyer_agreement', title: '', content: '' });
      setShowNewDoc(false);
      const response = await api.get(`/clients/${expandedClientId}`);
      setClientDetail(response.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to create document'));
    } finally {
      setSavingDoc(false);
    }
  };

  const handleSendDocument = async (documentId) => {
    setSendingDocId(documentId);
    try {
      const response = await api.post(`/documents/${documentId}/send`);
      if (response.data.email?.success) {
        toast.success('Document sent! Email delivered to client.');
      } else {
        toast.error(`Document sent, but email failed: ${response.data.email?.error || 'unknown error'}`);
      }
      const detail = await api.get(`/clients/${expandedClientId}`);
      setClientDetail(detail.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to send document'));
    } finally {
      setSendingDocId(null);
    }
  };

  const statusBadge = (status) => {
    const colors = {
      draft: 'bg-gray-500/30 text-gray-200',
      sent: 'bg-blue-500/30 text-blue-200',
      signed: 'bg-green-500/30 text-green-200',
    };
    return colors[status] || colors.draft;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white p-4 sm:p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <button onClick={() => navigate('/dashboard')} className="text-purple-300 text-sm mb-2 hover:text-white">
              ← Back to Dashboard
            </button>
            <h1 className="text-2xl font-bold">👥 Clients</h1>
          </div>
          <button
            onClick={() => setShowAddClient(!showAddClient)}
            className="bg-gradient-to-r from-purple-600 to-pink-600 px-5 py-2.5 rounded-lg font-semibold hover:shadow-lg transition-all"
          >
            {showAddClient ? 'Cancel' : '+ Add Client'}
          </button>
        </div>

        <AnimatePresence>
          {showAddClient && (
            <motion.form
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              onSubmit={handleAddClient}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20 mb-6 overflow-hidden"
            >
              <div className="grid grid-cols-2 gap-3 mb-3">
                <input required name="first_name" value={clientForm.first_name} onChange={handleClientFormChange}
                  placeholder="First name" className="px-3 py-2 rounded-lg bg-white/10 border border-white/20 placeholder-white/50" />
                <input required name="last_name" value={clientForm.last_name} onChange={handleClientFormChange}
                  placeholder="Last name" className="px-3 py-2 rounded-lg bg-white/10 border border-white/20 placeholder-white/50" />
              </div>
              <input required type="email" name="email" value={clientForm.email} onChange={handleClientFormChange}
                placeholder="Email" className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 placeholder-white/50 mb-3" />
              <div className="grid grid-cols-2 gap-3 mb-4">
                <input name="phone" value={clientForm.phone} onChange={handleClientFormChange}
                  placeholder="Phone (optional)" className="px-3 py-2 rounded-lg bg-white/10 border border-white/20 placeholder-white/50" />
                <select name="client_type" value={clientForm.client_type} onChange={handleClientFormChange}
                  className="px-3 py-2 rounded-lg bg-white/10 border border-white/20">
                  <option value="buyer" className="text-black">Buyer</option>
                  <option value="seller" className="text-black">Seller</option>
                  <option value="both" className="text-black">Both</option>
                </select>
              </div>
              <button type="submit" disabled={savingClient}
                className="w-full bg-purple-600 py-2.5 rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50">
                {savingClient ? 'Saving...' : 'Save Client'}
              </button>
            </motion.form>
          )}
        </AnimatePresence>

        {loading ? (
          <div className="text-center py-12 text-purple-200">Loading clients...</div>
        ) : clients.length === 0 ? (
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20 text-center text-purple-200">
            No clients yet. Add your first client to get started.
          </div>
        ) : (
          <div className="space-y-3">
            {clients.map((client) => (
              <div key={client.id} className="bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 overflow-hidden">
                <button
                  onClick={() => toggleClient(client.id)}
                  className="w-full flex justify-between items-center p-4 text-left hover:bg-white/5 transition-colors"
                >
                  <div>
                    <div className="font-semibold">{client.first_name} {client.last_name}</div>
                    <div className="text-sm text-purple-300">{client.email} · {client.client_type}</div>
                  </div>
                  <span className="text-purple-300">{expandedClientId === client.id ? '▲' : '▼'}</span>
                </button>

                <AnimatePresence>
                  {expandedClientId === client.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="border-t border-white/10 overflow-hidden"
                    >
                      <div className="p-4">
                        {loadingDetail ? (
                          <div className="text-center py-4 text-purple-200">Loading...</div>
                        ) : (
                          <>
                            <div className="flex justify-between items-center mb-3">
                              <h3 className="font-semibold text-sm text-purple-200">Documents</h3>
                              <button
                                onClick={() => setShowNewDoc(!showNewDoc)}
                                className="text-sm bg-purple-600/50 px-3 py-1.5 rounded-lg hover:bg-purple-600/70"
                              >
                                {showNewDoc ? 'Cancel' : '+ New Document'}
                              </button>
                            </div>

                            <AnimatePresence>
                              {showNewDoc && (
                                <motion.form
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: 'auto' }}
                                  exit={{ opacity: 0, height: 0 }}
                                  onSubmit={handleCreateDocument}
                                  className="bg-black/20 rounded-lg p-4 mb-4 overflow-hidden"
                                >
                                  <select name="document_type" value={docForm.document_type} onChange={handleDocFormChange}
                                    className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 mb-3">
                                    {DOCUMENT_TYPES.map((t) => (
                                      <option key={t.value} value={t.value} className="text-black">{t.label}</option>
                                    ))}
                                  </select>
                                  <input required name="title" value={docForm.title} onChange={handleDocFormChange}
                                    placeholder="Document title" className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 placeholder-white/50 mb-3" />
                                  <textarea required name="content" value={docForm.content} onChange={handleDocFormChange}
                                    placeholder="Document content" rows={5}
                                    className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 placeholder-white/50 mb-3" />
                                  <button type="submit" disabled={savingDoc}
                                    className="w-full bg-purple-600 py-2 rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50">
                                    {savingDoc ? 'Creating...' : 'Create Document'}
                                  </button>
                                </motion.form>
                              )}
                            </AnimatePresence>

                            {clientDetail?.documents?.length > 0 ? (
                              <div className="space-y-2">
                                {clientDetail.documents.map((doc) => (
                                  <div key={doc.id} className="flex justify-between items-center bg-black/20 rounded-lg p-3">
                                    <div>
                                      <div className="text-sm font-medium">{doc.title}</div>
                                      <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadge(doc.status)}`}>
                                        {doc.status}
                                      </span>
                                    </div>
                                    {doc.status === 'draft' && (
                                      <button
                                        onClick={() => handleSendDocument(doc.id)}
                                        disabled={sendingDocId === doc.id}
                                        className="text-sm bg-blue-600/50 px-3 py-1.5 rounded-lg hover:bg-blue-600/70 disabled:opacity-50"
                                      >
                                        {sendingDocId === doc.id ? 'Sending...' : 'Send'}
                                      </button>
                                    )}
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-sm text-purple-300 text-center py-3">No documents yet</div>
                            )}
                          </>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Clients;
