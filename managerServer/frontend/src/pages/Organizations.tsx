import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { OrganizationUnit, CreateOrganizationRequest } from '../types';
import './Organizations.css';

const Organizations: React.FC = () => {
  const [organizations, setOrganizations] = useState<OrganizationUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState<CreateOrganizationRequest>({
    name: '',
    description: '',
  });

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    setLoading(true);
    try {
      const data = await api.listOrganizations();
      setOrganizations(data.organizations);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createOrganization(formData);
      setShowCreateModal(false);
      resetForm();
      loadOrganizations();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create organization');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
    });
  };

  return (
    <div className="organizations-container">
      <div className="organizations-header">
        <h1>Organization Units</h1>
        <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
          Create Organization
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading organizations...</p>
        </div>
      ) : (
        <div className="organizations-grid">
          {organizations.map((org) => (
            <div key={org.id} className="org-card">
              <h3>{org.name}</h3>
              <p className="org-description">{org.description || 'No description'}</p>
              <div className="org-meta">
                <div className="meta-item">
                  <span className="meta-label">ID:</span>
                  <span className="meta-value">{org.id}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Created:</span>
                  <span className="meta-value">{new Date(org.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
          {organizations.length === 0 && (
            <div className="no-data">
              <p>No organizations found. Create one to get started.</p>
            </div>
          )}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Organization</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label htmlFor="name">Name</label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="Enter organization name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter description (optional)"
                  rows={4}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Organizations;
