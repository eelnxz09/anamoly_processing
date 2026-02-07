import React, { useState, useCallback } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react';

const UploadSection = ({ onUploadSuccess, apiBaseUrl }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange({ target: { files: e.dataTransfer.files } });
    }
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        return;
      }
      setFile(selectedFile);
      setError(null);
      setSuccess(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiBaseUrl}/upload/csv`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setSuccess(`Successfully uploaded ${data.row_count} transactions`);
      setFile(null);
      
      if (onUploadSuccess) {
        onUploadSuccess(data.metadata);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="upload-section">
      <div className="section-header">
        <h2 className="page-title">Upload Transaction Data</h2>
        <p className="page-subtitle">Upload CSV files with transaction history for analysis</p>
      </div>

      <div className="upload-container">
        {/* Drop Zone */}
        <div
          className={`drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="file-input"
            id="file-upload"
          />
          
          {!file ? (
            <label htmlFor="file-upload" className="drop-zone-content">
              <Upload size={48} className="upload-icon" />
              <h3>Drop CSV file here or click to browse</h3>
              <p>Supports .csv files with transaction data</p>
            </label>
          ) : (
            <div className="file-preview">
              <FileText size={48} className="file-icon" />
              <div className="file-info">
                <h3>{file.name}</h3>
                <p>{(file.size / 1024).toFixed(2)} KB</p>
              </div>
              <button className="btn-icon" onClick={clearFile}>
                <X size={20} />
              </button>
            </div>
          )}
        </div>

        {/* Upload Button */}
        {file && (
          <button
            className="btn btn-primary btn-large"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <div className="spinner"></div>
                Uploading...
              </>
            ) : (
              <>
                <Upload size={20} />
                Upload & Process
              </>
            )}
          </button>
        )}

        {/* Messages */}
        {error && (
          <div className="alert alert-error">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            <CheckCircle size={20} />
            <span>{success}</span>
          </div>
        )}

        {/* Requirements */}
        <div className="requirements-card">
          <h4>CSV Format Requirements</h4>
          <ul className="requirements-list">
            <li>
              <span className="requirement-label">Required columns:</span>
              <code>amount</code>, <code>timestamp</code>
            </li>
            <li>
              <span className="requirement-label">Optional columns:</span>
              <code>user_id</code>, <code>merchant_category</code>, <code>location</code>, <code>device_type</code>
            </li>
            <li>
              <span className="requirement-label">Minimum rows:</span>
              10 transactions (recommended 100+ for better accuracy)
            </li>
            <li>
              <span className="requirement-label">Date format:</span>
              ISO 8601 (YYYY-MM-DD HH:MM:SS) or any standard format
            </li>
          </ul>
        </div>

        {/* Sample Data */}
        <div className="sample-section">
          <h4>Example CSV Format</h4>
          <div className="code-block">
            <pre>
{`amount,timestamp,user_id,merchant_category,location
250.00,2024-01-15 14:30:00,user_001,retail,new_york
1500.00,2024-01-15 15:45:00,user_002,electronics,los_angeles
75.50,2024-01-15 16:20:00,user_001,food,new_york`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadSection;
