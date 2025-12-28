/** Simple export button for CSV and JSON formats. */

import React, { useState } from "react";
import { Button, Dropdown, App } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import type { MenuProps } from "antd";
import type { ExportFormat } from "../../types/export";

interface ExportButtonProps {
  databaseName: string;
  sql: string;
  disabled?: boolean;
}

export const ExportButton: React.FC<ExportButtonProps> = ({
  databaseName,
  sql,
  disabled = false,
}) => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);

  const handleExport = async (format: ExportFormat) => {
    setLoading(true);
    try {
      // Direct export without size checking
      const response = await fetch(`/api/v1/export/${databaseName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql, format })
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export.${format === 'csv' ? 'csv' : 'json'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      message.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      message.error('Export failed');
    } finally {
      setLoading(false);
    }
  };

  const menuItems: MenuProps["items"] = [
    {
      key: "csv",
      label: "Export as CSV",
      onClick: () => handleExport("csv"),
    },
    {
      key: "json",
      label: "Export as JSON",
      onClick: () => handleExport("json"),
    },
  ];

  return (
    <Dropdown menu={{ items: menuItems }} disabled={disabled || loading}>
      <Button loading={loading} icon={<DownloadOutlined />}>
        Export
      </Button>
    </Dropdown>
  );
};
