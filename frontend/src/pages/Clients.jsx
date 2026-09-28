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

const PIPELINE_STAGES = [
  { value: 'new_lead', label: 'New Lead', color: 'bg-slate-500' },
  { value: 'contacted', label: 'Contacted', color: 'bg-blue-500' },
  { value: 'qualified', label: 'Qualified', color: 'bg-cyan-500' },
  { value: 'showing', label: 'Showing', color: 'bg-purple-500' },
  { value: 'offer', label: 'Offer', color: 'bg-orange-500' },
  { value: 'escrow', label: 'Escrow', color: 'bg-yellow-500' },
  { value: 'closed', label: 'Closed', color: 'bg-green-500' },
];

const ACTIVITY_TYPES = [
  { value: 'note', label: '📝 Note' },
  { value: 'call', label: '📞 Call' },
  { value: 'text', label: '💬 Text' },
  { value: 'email', label: '✉️ Email' },
  { value: 'property_viewed', label: '🏠 Property Viewed' },
  { value: 'appointment', label: '📅 Appointment' },
];

const stageMeta = (value) => PIPELINE_STAGES.find((s) => s.value === value) || PIPELINE_STAGES[0];

const Clients = () => {
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddClient, setShowAddClient] = useState(false);
  const [savingClient, setSavingClient] = useState(false);
  const [expandedClientId, setExpandedClientId] = useState(null);
  const [clientDetail, setClientDetail] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [showNewDoc, setShowNewDoc] = useState(false);
  const [savingDoc, setSavingDoc] = useState(false);
  const [sendingDocId, setSendingDocId] = useState(null);
  const [activeTab, setActiveTab] = useState('activity');
  const [savingActivity, setSavingActivity] = useState(false);
  const [savingTask, setSavingTask] = useState(false);

  const [clientForm, setClientForm] = useState({
    first_name: '', last_name: '', email: '', phone: '', client_type: 'buyer',
  });

  const [docForm, setDocForm] = useState({
    document_type: 'buyer_agreement', title: '', content: '',
  });

  const [activityForm, setActivityForm] = useState({ activity_type: 'note', description: '' });
  const [taskForm, setTaskForm] = useState({ title: '', due_date: '' });

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

  const loadClientDetail = async (clientId) => {
    setLoadingDetail(true);
    try {
      const [detailRes, tasksRes] = await Promise.all([
        api.get(`/clients/${clientId}`),
        api.get('/tasks', { params: { client_id: clientId } }),
      ]);
      setClientDetail(detailRes.data);
      setTasks(tasksRes.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to load client details'));
    } finally {
      setLoadingDetail(false);
    }
  };

  const toggleClient = async (clientId) => {
    if (expandedClientId === clientId) {
      setExpandedClientId(null);
      setClientDetail(null);
      setTasks([]);
      setShowNewDoc(false);
      return;
    }
    setExpandedClientId(clientId);
    setShowNewDoc(false);
    setActiveTab('activity');
    await loadClientDetail(clientId);
  };

  const handleStageChange = async (clientId, newStage) => {
    try {
      await api.put(`/clients/${clientId}/pipeline-stage`, null, { params: { stage: newStage } });
      toast.success('Pipeline stage updated');
      fetchClients();
      if (expandedClientId === clientId) {
        loadClientDetail(clientId);
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to update stage'));
    }
  };

  const handleActivityFormChange = (e) => {
    const { name, value } = e.target;
    setActivityForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleLogActivity = async (e) => {
    e.preventDefault();
    if (!activityForm.description.trim()) {
      toast.error('Enter a description first');
      return;
    }
    setSavingActivity(true);
    try {
      await api.post(`/clients/${expandedClientId}/activity`, activityForm);
      toast.success('Activity logged');
      setActivityForm({ activity_type: 'note', description: '' });
      loadClientDetail(expandedClientId);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to log activity'));
    } finally {
      setSavingActivity(false);
    }
  };

  const handleTaskFormChange = (e) => {
    const { name, value } = e.target;
    setTaskForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!taskForm.title.trim()) {
      toast.error('Enter a task title');
      return;
    }
    setSavingTask(true);
    try {
      const payload = { title: taskForm.title };
      if (taskForm.due_date) {
        payload.due_date = new Date(taskForm.due_date).toISOString();
      }
      await api.post(`/clients/${expandedClientId}/tasks`, payload);
      toast.success('Task added');
      setTaskForm({ title: '', due_date: '' });
      loadClientDetail(expandedClientId);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to add task'));
    } finally {
      setSavingTask(false);
    }
  };

  const handleToggleTask = async (taskId, completed) => {
    try {
      await api.put(`/tasks/${taskId}`, { completed: !completed });
      loadClientDetail(expandedClientId);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to update task'));
    }
  };

  const handleDocFormChange = (e) => {
    const { name, value } = e.target;
    if (name === 'document_type') {
      const template = window.__docTemplates?.find((t) => t.document_type === value);
      setDocForm({
        document_type: value,
        title: template?.name || docForm.title,
        content: template?.content || docForm.content,
      });
    } else {
      setDocForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const openNewDoc = async () => {
    setShowNewDoc(!showNewDoc);
    if (!window.__docTemplates) {
      try {
        const response = await api.get('/templates');
        window.__docTemplates = response.data;
        const first = response.data.find((t) => t.document_type === docForm.document_type);
        if (first) {
          setDocForm((prev) => ({ ...prev, title: first.name, content: first.content }));
        }
      } catch (error) {
        // templates are optional - agent can still type content manually
      }
    }
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
      loadClientDetail(expandedClientId);
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
      loadClientDetail(expandedClientId);
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

  const activityIcon = (type) => ACTIVITY_TYPES.find((a) => a.value === type)?.label.split(' ')[0] || '•';

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
            {clients.map((client) => {
              const meta = stageMeta(client.pipeline_stage);
              return (
                <div key={client.id} className="bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 overflow-hidden">
                  <button
                    onClick={() => toggleClient(client.id)}
                    className="w-full flex justify-between items-center p-4 text-left hover:bg-white/5 transition-colors"
                  >
                    <div>
                      <div className="font-semibold">{client.first_name} {client.last_name}</div>
                      <div className="text-sm text-purple-300">{client.email} · {client.client_type}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${meta.color} text-white font-medium`}>
                        {meta.label}
                      </span>
                      <span className="text-purple-300">{expandedClientId === client.id ? '▲' : '▼'}</span>
                    </div>
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
                          {/* Pipeline stage selector */}
                          <div className="mb-4">
                            <div className="text-xs text-purple-300 mb-2">Pipeline Stage</div>
                            <div className="flex flex-wrap gap-1.5">
                              {PIPELINE_STAGES.map((stage) => (
                                <button
                                  key={stage.value}
                                  onClick={() => handleStageChange(client.id, stage.value)}
                                  className={`text-xs px-2.5 py-1.5 rounded-full font-medium transition-all ${
                                    client.pipeline_stage === stage.value
                                      ? `${stage.color} text-white`
                                      : 'bg-white/10 text-purple-300 hover:bg-white/20'
                                  }`}
                                >
                                  {stage.label}
                                </button>
                              ))}
                            </div>
                          </div>

                          {loadingDetail ? (
                            <div className="text-center py-4 text-purple-200">Loading...</div>
                          ) : (
                            <>
                              {/* Tabs */}
                              <div className="flex gap-1 mb-3 border-b border-white/10">
                                {['activity', 'tasks', 'documents'].map((tab) => (
                                  <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-3 py-2 text-sm font-medium capitalize border-b-2 transition-all ${
                                      activeTab === tab
                                        ? 'border-purple-400 text-white'
                                        : 'border-transparent text-purple-300 hover:text-white'
                                    }`}
                                  >
                                    {tab}
                                    {tab === 'tasks' && tasks.filter((t) => !t.completed).length > 0 && (
                                      <span className="ml-1.5 bg-pink-500 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                                        {tasks.filter((t) => !t.completed).length}
                                      </span>
                                    )}
                                  </button>
                                ))}
                              </div>

                              {/* Activity tab */}
                              {activeTab === 'activity' && (
                                <div>
                                  <form onSubmit={handleLogActivity} className="bg-black/20 rounded-lg p-3 mb-3">
                                    <div className="flex gap-2 mb-2">
                                      <select
                                        name="activity_type"
                                        value={activityForm.activity_type}
                                        onChange={handleActivityFormChange}
                                        className="px-2 py-1.5 rounded-lg bg-white/10 border border-white/20 text-sm"
                                      >
                                        {ACTIVITY_TYPES.map((t) => (
                                          <option key={t.value} value={t.value} className="text-black">{t.label}</option>
                                        ))}
                                      </select>
                                      <input
                                        name="description"
                                        value={activityForm.description}
                                        onChange={handleActivityFormChange}
                                        placeholder="What happened?"
                                        className="flex-1 px-3 py-1.5 rounded-lg bg-white/10 border border-white/20 placeholder-white/50 text-sm"
                                      />
                                    </div>
                                    <button type="submit" disabled={savingActivity}
                                      className="w-full bg-purple-600/70 py-1.5 rounded-lg text-sm font-medium hover:bg-purple-600 disabled:opacity-50">
                                      {savingActivity ? 'Logging...' : 'Log Activity'}
                                    </button>
                                  </form>

                                  {clientDetail?.activity?.length > 0 ? (
                                    <div className="space-y-2">
                                      {clientDetail.activity.map((entry) => (
                                        <div key={entry.id} className="flex gap-2 bg-black/20 rounded-lg p-3 text-sm">
                                          <span>{activityIcon(entry.activity_type)}</span>
                                          <div className="flex-1">
                                            <div>{entry.description}</div>
                                            <div className="text-xs text-purple-400 mt-0.5">
                                              {new Date(entry.created_at).toLocaleString()}
                                            </div>
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <div className="text-sm text-purple-300 text-center py-3">No activity logged yet</div>
                                  )}
                                </div>
                              )}

                              {/* Tasks tab */}
                              {activeTab === 'tasks' && (
                                <div>
                                  <form onSubmit={handleAddTask} className="bg-black/20 rounded-lg p-3 mb-3">
                                    <div className="flex gap-2 mb-2">
                                      <input
                                        name="title"
                                        value={taskForm.title}
                                        onChange={handleTaskFormChange}
                                        placeholder="Follow-up task"
                                        className="flex-1 px-3 py-1.5 rounded-lg bg-white/10 border border-white/20 placeholder-white/50 text-sm"
                                      />
                                      <input
                                        type="date"
                                        name="due_date"
                                        value={taskForm.due_date}
                                        onChange={handleTaskFormChange}
                                        className="px-2 py-1.5 rounded-lg bg-white/10 border border-white/20 text-sm"
                                      />
                                    </div>
                                    <button type="submit" disabled={savingTask}
                                      className="w-full bg-purple-600/70 py-1.5 rounded-lg text-sm font-medium hover:bg-purple-600 disabled:opacity-50">
                                      {savingTask ? 'Adding...' : 'Add Task'}
                                    </button>
                                  </form>

                                  {tasks.length > 0 ? (
                                    <div className="space-y-2">
                                      {tasks.map((task) => (
                                        <div key={task.id} className="flex items-center gap-3 bg-black/20 rounded-lg p-3">
                                          <input
                                            type="checkbox"
                                            checked={task.completed}
                                            onChange={() => handleToggleTask(task.id, task.completed)}
                                            className="w-4 h-4"
                                          />
                                          <div className="flex-1">
                                            <div className={`text-sm ${task.completed ? 'line-through text-purple-400' : ''}`}>
                                              {task.title}
                                            </div>
                                            {task.due_date && (
                                              <div className="text-xs text-purple-400">
                                                Due {new Date(task.due_date).toLocaleDateString()}
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <div className="text-sm text-purple-300 text-center py-3">No follow-up tasks yet</div>
                                  )}
                                </div>
                              )}

                              {/* Documents tab */}
                              {activeTab === 'documents' && (
                                <div>
                                  <div className="flex justify-between items-center mb-3">
                                    <h3 className="font-semibold text-sm text-purple-200">Documents</h3>
                                    <button
                                      onClick={openNewDoc}
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
                                          placeholder="Document content" rows={8}
                                          className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 placeholder-white/50 mb-3 font-mono text-xs" />
                                        <p className="text-xs text-purple-400 mb-3">
                                          Template loaded automatically - fill in the {'{brackets}'} before sending.
                                        </p>
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
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Clients;
