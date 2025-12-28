/** Export button component for triggering data exports. */

import React, { useState } from "react";
import { Button, Dropdown, Modal, App } from "antd";
import { DownloadOutlined, FileTextOutlined, FileOutlined, FileMarkdownOutlined } from "@ant-design/icons";
import type { MenuProps } from "antd";
import type { ExportFormat, ExportOptions } from "../../types/export";
import { exportService } from "../../services/export";

interface ExportButtonProps {
  databaseName: string;
  sql: string;
  disabled?: boolean;
  className?: string;
}

/**
 * Export button component with format selection dropdown.
 *
 * @param databaseName - Database connection name
 * @param sql - SQL query to export
 * @param disabled - Whether button is disabled
 * @param className - Optional CSS class name
 */
export const ExportButton: React.FC<ExportButtonProps> = ({
  databaseName,
  sql,
  disabled = false,
  className,
}) => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  /**
   * Handle export with format selection.
   */
  const handleExport = async (format: ExportFormat) => {
    setLoading(true);

    try {
      // Step 1: Check file size
      const checkResponse = await exportService.checkExportSize(databaseName, {
        sql,
        format,
        useSampling: true,
        sampleSize: 100,
      });

      // Step 2: Show warning if needed
      if (!checkResponse.allowed) {
        Modal.error({
          title: "Export Not Allowed",
          content: (
            <div>
              <p>{checkResponse.warning}</p>
              <p>{checkResponse.recommendation}</p>
            </div>
          ),
        });
        setLoading(false);
        return;
      }

      if (checkResponse.warning) {
        Modal.confirm({
          title: "Large Export Warning",
          content: (
            <div>
              <p>{checkResponse.warning}</p>
              <p>Estimated size: {checkResponse.estimatedSize.estimatedMb.toFixed(2)} MB</p>
            </div>
          ),
          onOk: () => executeExport(format),
          onCancel: () => setLoading(false),
        });
      } else {
        executeExport(format);
      }
    } catch (error: any) {
      message.error(`Export check failed: ${error.message}`);
      setLoading(false);
    }
  };

  /**
   * Execute export task and poll for completion.
   */
  const executeExport = async (format: ExportFormat) => {
    try {
      // Step 3: Create export task
      const taskResponse = await exportService.createExportTask(databaseName, {
        sql,
        format,
        exportAll: true,
      });

      setCurrentTaskId(taskResponse.taskId);

      // Step 4: Poll for completion
      const finalTask = await exportService.pollTaskStatus(
        taskResponse.taskId,
        (task) => {
          // Update progress
          if (task.progress % 20 === 0) {
            message.loading(`Exporting... ${task.progress}%`, 0);
          }
        },
        1000
      );

      // Clear loading message
      message.destroy();

      // Step 5: Download file
      if (finalTask.fileUrl) {
        const filename = finalTask.fileUrl.split("/").pop() || "export";
        exportService.downloadFile(filename);
        message.success(`Export completed: ${finalTask.rowCount} rows exported`);
      }

      setCurrentTaskId(null);
      setLoading(false);
    } catch (error: any) {
      message.destroy();
      message.error(`Export failed: ${error.message}`);
      setCurrentTaskId(null);
      setLoading(false);
    }
  };

  /**
   * Export format menu items.
   */
  const menuItems: MenuProps["items"] = [
    {
      key: "csv",
      icon: <FileTextOutlined />,
      label: "Export as CSV",
      onClick: () => handleExport("csv"),
    },
    {
      key: "json",
      icon: <FileOutlined />,
      label: "Export as JSON",
      onClick: () => handleExport("json"),
    },
    {
      key: "markdown",
      icon: <FileMarkdownOutlined />,
      label: "Export as Markdown",
      onClick: () => handleExport("markdown"),
    },
  ];

  return (
    <Dropdown
      menu={{ items: menuItems }}
      trigger={["click"]}
      disabled={disabled || loading}
    >
      <Button
        type="primary"
        icon={<DownloadOutlined />}
        loading={loading}
        className={className}
      >
        Export
      </Button>
    </Dropdown>
  );
};

export default ExportButton;
