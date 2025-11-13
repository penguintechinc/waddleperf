import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { User, CreateUserRequest, UpdateUserRequest, OrganizationUnit, UserRole } from '../types';
import './Users.css';

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [organizations, setOrganizations] = useState<OrganizationUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [page, setPage] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);

  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    email: '',
    password: '',
    role: 'user',
    ou_id: undefined,
  });

  const [editFormData, setEditFormData] = useState<UpdateUserRequest>({
    email: '',
    role: 'user',
    ou_id: undefined,
    is_active: true,
  });

  useEffect(() => {
    loadUsers();
    loadOrganizations();
  }, [page]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await api.listUsers(page, 50);
      setUsers(data.users);
      setTotalUsers(data.total);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizations = async () => {
    try {
      const data = await api.listOrganizations();
      setOrganizations(data.organizations);
    } catch (err: any) {
      console.error('Failed to load organizations:', err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createUser(formData);
      setShowCreateModal(false);
      resetForm();
      loadUsers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create user');
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;

    try {
      await api.updateUser(currentUser.id, editFormData);
      setShowEditModal(false);
      setCurrentUser(null);
      loadUsers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update user');
    }
  };

  const handleDelete = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      await api.deleteUser(userId);
      loadUsers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete user');
    }
  };

  const openEditModal = (user: User) => {
    setCurrentUser(user);
    setEditFormData({
      email: user.email,
      role: user.role,
      ou_id: user.ou_id || undefined,
      is_active: user.is_active,
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      role: 'user',
      ou_id: undefined,
    });
  };

  const roles: UserRole[] = ['global_admin', 'global_reporter', 'ou_admin', 'ou_reporter', 'user'];

  return (
    <div className="users-container">
      <div className="users-header">
        <h1>User Management</h1>
        <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
          Create User
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading users...</p>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="users-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Organization</th>
                  <th>MFA</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.username}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className="role-badge">{user.role}</span>
                    </td>
                    <td>
                      {user.ou_id
                        ? organizations.find((o) => o.id === user.ou_id)?.name || user.ou_id
                        : 'N/A'}
                    </td>
                    <td>{user.mfa_enabled ? 'Enabled' : 'Disabled'}</td>
                    <td>
                      <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button className="btn-sm btn-edit" onClick={() => openEditModal(user)}>
                        Edit
                      </button>
                      <button className="btn-sm btn-delete" onClick={() => handleDelete(user.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
              Previous
            </button>
            <span>
              Page {page} of {Math.ceil(totalUsers / 50)}
            </span>
            <button onClick={() => setPage((p) => p + 1)} disabled={users.length < 50}>
              Next
            </button>
          </div>
        </>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New User</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="role">Role</label>
                <select
                  id="role"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
                >
                  {roles.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="ou_id">Organization (Optional)</label>
                <select
                  id="ou_id"
                  value={formData.ou_id || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, ou_id: e.target.value ? parseInt(e.target.value) : undefined })
                  }
                >
                  <option value="">None</option>
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
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

      {showEditModal && currentUser && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Edit User: {currentUser.username}</h2>
            <form onSubmit={handleEdit}>
              <div className="form-group">
                <label htmlFor="edit-email">Email</label>
                <input
                  id="edit-email"
                  type="email"
                  value={editFormData.email}
                  onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="edit-role">Role</label>
                <select
                  id="edit-role"
                  value={editFormData.role}
                  onChange={(e) => setEditFormData({ ...editFormData, role: e.target.value as UserRole })}
                >
                  {roles.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="edit-ou_id">Organization</label>
                <select
                  id="edit-ou_id"
                  value={editFormData.ou_id || ''}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, ou_id: e.target.value ? parseInt(e.target.value) : undefined })
                  }
                >
                  <option value="">None</option>
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={editFormData.is_active}
                    onChange={(e) => setEditFormData({ ...editFormData, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowEditModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Update
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;
