import { React } from "../deps.mjs";

const h = React.createElement;

function buildReplayPairOptionGroups(options) {
  const rows = Array.isArray(options) ? options : [];
  const groups = {
    latest_window: [],
    retained_extra: [],
    other: [],
  };
  rows.forEach((row) => {
    const state = String(row?.retentionState || "").trim();
    if (state === "latest_window") {
      groups.latest_window.push(row);
      return;
    }
    if (state === "retained_extra") {
      groups.retained_extra.push(row);
      return;
    }
    groups.other.push(row);
  });
  return [
    groups.latest_window.length > 0
      ? { id: "latest_window", label: "Latest Window", options: groups.latest_window }
      : null,
    groups.retained_extra.length > 0
      ? { id: "retained_extra", label: "Extra Preserved", options: groups.retained_extra }
      : null,
    groups.other.length > 0
      ? { id: "other", label: "Other", options: groups.other }
      : null,
  ].filter(Boolean);
}

export function DecisionPane({
  baselineId,
  compareGraphRunId,
  setCompareGraphRunId,
  loadCompareGraphRunById,
  clearCompareGraphRun,
  pinCurrentGraphRunAsCompare,
  pinBaselineFromGraphRun,
  runPolicyGateForGraphRun,
  runDecisionRegressionSession,
  runLowVsCurrentTrackCompare,
  trackCompareBaselinePresetId,
  setTrackCompareBaselinePresetId,
  trackCompareTargetPresetId,
  setTrackCompareTargetPresetId,
  trackComparePresetOptions,
  trackCompareQuickPairOptions,
  applyTrackCompareQuickPair,
  trackCompareSelectedPairSummaryText,
  trackCompareSelectedPairForecastText,
  pinnedCompareQuickActionOptions,
  pinnedCompareQuickActionSummaryText,
  pinnedCompareQuickActionDetailText,
  expandedPinnedCompareQuickActionId,
  applyPinnedCompareQuickAction,
  runPinnedCompareQuickAction,
  togglePinnedCompareQuickActionExpanded,
  compareSessionHistoryText,
  compareReplayPairOptions,
  selectedCompareReplayPairId,
  setSelectedCompareReplayPairId,
  selectedCompareReplayPairLabelDraft,
  setSelectedCompareReplayPairLabelDraft,
  latestReplayableCompareSessionText,
  canReplayLatestCompareSession,
  applyLatestCompareSessionPair,
  runLatestCompareSessionPair,
  selectedReplayableCompareSessionText,
  selectedReplayableCompareSessionMetaText,
  selectedReplayableCompareSessionRetentionText,
  selectedReplayableCompareSessionArtifactExpectationText,
  selectedReplayableCompareSessionPreviewText,
  canReplaySelectedCompareSession,
  applySelectedCompareSessionPair,
  runSelectedCompareSessionPair,
  saveSelectedCompareSessionPairLabel,
  togglePinSelectedCompareSessionPair,
  deleteSelectedCompareSessionPair,
  compareSessionImportFileInputRef,
  compareSessionRetentionPolicy,
  compareSessionRetentionPolicyOptions,
  compareSessionRetentionPolicySummaryText,
  compareSessionRetentionGroupHintText,
  compareSessionRetentionPreviewText,
  compareSessionTransferCompactSummaryText,
  compareSessionTransferStatusText,
  compareSessionTransferBadgeRows,
  hasCompareSessionImportPreview,
  compareSessionImportPreviewSummaryText,
  compareSessionImportPreviewText,
  triggerCompareSessionImportFilePick,
  handleCompareSessionImportFileChange,
  updateCompareSessionRetentionPolicy,
  clearAllCompareSessionHistory,
  applyCompareSessionImportPreview,
  clearCompareSessionImportPreview,
  exportCompareSessionHistory,
  runPresetPairTrackCompare,
  exportGateReport,
  exportDecisionRegressionSession,
  exportDecisionBriefMd,
  currentTrackLabel,
  compareTrackLabel,
  trackCompareGuideText,
  decisionSummaryText,
  decisionOpsStatusText,
  artifactInspectorDecisionStatusBadgesText,
  artifactInspectorDecisionStatusBadgeRows,
  artifactInspectorDecisionLayoutStateText,
  artifactInspectorDecisionProbeStateText,
  artifactInspectorDecisionLastActionText,
  artifactInspectorDecisionMaintenanceActionText,
  artifactInspectorDecisionMaintenanceLastClearText,
  artifactInspectorDecisionMaintenanceSummaryText,
  artifactInspectorDecisionMaintenanceOperatorSummaryText,
  artifactInspectorDecisionMaintenanceControlState,
  artifactInspectorDecisionRecentActionsText,
  artifactInspectorDecisionAuditStateText,
  artifactInspectorDecisionAuditCapacityText,
  artifactInspectorDecisionAuditWindowText,
  artifactInspectorDecisionAuditContinuityText,
  artifactInspectorDecisionAuditHealthText,
  artifactInspectorDecisionAuditHealthReasonText,
  artifactInspectorDecisionAuditNextActionText,
  artifactInspectorDecisionAuditOperatorSummaryText,
  artifactInspectorDecisionAuditSummaryText,
  artifactInspectorDecisionAuditControlState,
  artifactInspectorDecisionControlState,
  applyRecommendedArtifactInspectorAuditActionFromDecisionPane,
  clearArtifactInspectorActionTrailFromDecisionPane,
  clearArtifactInspectorMaintenanceActionFromDecisionPane,
  collapseArtifactInspectorEvidenceFromDecisionPane,
  expandArtifactInspectorEvidenceFromDecisionPane,
  resetArtifactInspectorLayoutFromDecisionPane,
  trackCompareRunnerStatusText,
  compareRunStatusText,
  lastRegressionSession,
  lastRegressionExport,
}) {
  const replayPairOptionGroups = buildReplayPairOptionGroups(compareReplayPairOptions);
  return h("div", { className: "field", key: "decision_surface" }, [
    h("label", { className: "label", key: "lbl_decision_surface" }, "Decision Pane"),
    h("div", { className: "hint", key: "decision_scope_hint" }, `baseline_id: ${String(baselineId || "-")}`),
    h("input", {
      className: "input",
      value: String(compareGraphRunId || ""),
      onChange: (e) => setCompareGraphRunId(String(e.target.value || "")),
      placeholder: "compare graph_run_id (grun_...)",
    }),
    h("div", { className: "btn-row", key: "decision_compare_row" }, [
      h("button", {
        className: "btn",
        key: "decision_load_compare",
        onClick: () => loadCompareGraphRunById(String(compareGraphRunId || ""), { mode: "manual" }),
      }, "Load Compare"),
      h("button", {
        className: "btn",
        key: "decision_pin_current_compare",
        onClick: pinCurrentGraphRunAsCompare,
      }, "Use Current as Compare"),
      h("button", {
        className: "btn",
        key: "decision_clear_compare",
        onClick: clearCompareGraphRun,
      }, "Clear Compare"),
    ]),
    h("div", { className: "field", key: "decision_track_workflow" }, [
      h("label", { className: "label", key: "lbl_decision_track_workflow" }, "Track Compare Workflow"),
      h("div", { className: "hint", key: "decision_current_track_hint" }, `current_track: ${String(currentTrackLabel || "-")}`),
      h("div", { className: "hint", key: "decision_compare_track_hint" }, `compare_track: ${String(compareTrackLabel || "-")}`),
      h("pre", { className: "result-box", key: "decision_track_workflow_box" }, String(trackCompareGuideText || "-")),
    ]),
    h("div", { className: "field", key: "decision_artifact_state_mirror" }, [
      h("label", { className: "label", key: "decision_artifact_state_mirror_label" }, "Inspector State Mirror"),
      h("div", { className: "btn-row", key: "decision_artifact_state_mirror_actions" }, [
        h("button", {
          className: "btn",
          key: "decision_collapse_artifact_inspector_evidence",
          onClick: collapseArtifactInspectorEvidenceFromDecisionPane,
          disabled: artifactInspectorDecisionControlState?.collapseDisabled === true,
        }, "Collapse Inspector Evidence"),
        h("button", {
          className: "btn",
          key: "decision_expand_artifact_inspector_evidence",
          onClick: expandArtifactInspectorEvidenceFromDecisionPane,
          disabled: artifactInspectorDecisionControlState?.expandDisabled === true,
        }, "Expand Inspector Evidence"),
        h("button", {
          className: "btn",
          key: "decision_reset_artifact_inspector_layout",
          onClick: resetArtifactInspectorLayoutFromDecisionPane,
          disabled: artifactInspectorDecisionControlState?.resetDisabled === true,
        }, "Reset Inspector Layout"),
        h("button", {
          className: "btn",
          key: "decision_apply_recommended_artifact_inspector_audit_action",
          onClick: applyRecommendedArtifactInspectorAuditActionFromDecisionPane,
          disabled: artifactInspectorDecisionAuditControlState?.applyRecommendedDisabled === true,
        }, "Apply Recommended Audit Action"),
        h("button", {
          className: "btn",
          key: "decision_clear_artifact_inspector_action_trail",
          onClick: clearArtifactInspectorActionTrailFromDecisionPane,
          disabled: artifactInspectorDecisionAuditControlState?.clearDisabled === true,
        }, "Clear Action Trail"),
        h("button", {
          className: "btn",
          key: "decision_clear_artifact_inspector_maintenance_action",
          onClick: clearArtifactInspectorMaintenanceActionFromDecisionPane,
          disabled: artifactInspectorDecisionMaintenanceControlState?.clearDisabled === true,
        }, "Clear Maintenance Marker"),
      ]),
      h("div", { className: "chip-list", key: "decision_artifact_inspector_live_state_chips" }, (
        Array.isArray(artifactInspectorDecisionStatusBadgeRows) && artifactInspectorDecisionStatusBadgeRows.length > 0
          ? artifactInspectorDecisionStatusBadgeRows
          : [{ label: "layout:unknown", tone: "status-neutral" }]
      ).map((row, idx) =>
        h("span", {
          className: `chip ${String(row?.tone || "status-neutral")}`,
          key: `decision_artifact_inspector_live_state_chip_${idx}`,
        }, String(row?.label || "-"))
      )),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_badges_hint" }, String(artifactInspectorDecisionStatusBadgesText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_layout_hint" }, String(artifactInspectorDecisionLayoutStateText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_probe_hint" }, String(artifactInspectorDecisionProbeStateText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_action_hint" }, String(artifactInspectorDecisionLastActionText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_maintenance_hint" }, String(artifactInspectorDecisionMaintenanceActionText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_maintenance_last_clear_hint" }, String(artifactInspectorDecisionMaintenanceLastClearText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_maintenance_summary_hint" }, String(artifactInspectorDecisionMaintenanceSummaryText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_maintenance_operator_summary_hint" }, String(artifactInspectorDecisionMaintenanceOperatorSummaryText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_maintenance_controls_hint" }, String(artifactInspectorDecisionMaintenanceControlState?.text || "artifact_inspector_maintenance_controls: -")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_recent_actions_hint" }, String(artifactInspectorDecisionRecentActionsText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_state_hint" }, String(artifactInspectorDecisionAuditStateText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_capacity_hint" }, String(artifactInspectorDecisionAuditCapacityText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_window_hint" }, String(artifactInspectorDecisionAuditWindowText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_continuity_hint" }, String(artifactInspectorDecisionAuditContinuityText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_health_hint" }, String(artifactInspectorDecisionAuditHealthText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_health_reason_hint" }, String(artifactInspectorDecisionAuditHealthReasonText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_next_action_hint" }, String(artifactInspectorDecisionAuditNextActionText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_operator_summary_hint" }, String(artifactInspectorDecisionAuditOperatorSummaryText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_summary_hint" }, String(artifactInspectorDecisionAuditSummaryText || "-")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_audit_controls_hint" }, String(artifactInspectorDecisionAuditControlState?.text || "artifact_inspector_audit_controls: -")),
      h("div", { className: "hint", key: "decision_artifact_inspector_live_state_controls_hint" }, String(artifactInspectorDecisionControlState?.text || "artifact_inspector_controls: -")),
    ]),
    h("div", { className: "field", key: "decision_preset_pair_compare" }, [
      h("label", { className: "label", key: "decision_preset_pair_label" }, "Preset Pair Compare"),
      h("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }, key: "decision_preset_pair_grid" }, [
        h("div", { key: "decision_preset_pair_baseline_col" }, [
          h("div", { className: "hint", key: "decision_preset_pair_baseline_hint" }, "baseline_preset"),
          h("select", {
            className: "select",
            value: String(trackCompareBaselinePresetId || ""),
            onChange: (e) => setTrackCompareBaselinePresetId(String(e.target.value || "")),
          }, (Array.isArray(trackComparePresetOptions) ? trackComparePresetOptions : []).map((row) =>
            h("option", { key: `decision_compare_baseline_${String(row?.id || "")}`, value: String(row?.id || "") }, String(row?.label || row?.id || "-"))
          )),
        ]),
        h("div", { key: "decision_preset_pair_target_col" }, [
          h("div", { className: "hint", key: "decision_preset_pair_target_hint" }, "target_preset"),
          h("select", {
            className: "select",
            value: String(trackCompareTargetPresetId || ""),
            onChange: (e) => setTrackCompareTargetPresetId(String(e.target.value || "")),
          }, (Array.isArray(trackComparePresetOptions) ? trackComparePresetOptions : []).map((row) =>
            h("option", { key: `decision_compare_target_${String(row?.id || "")}`, value: String(row?.id || "") }, String(row?.label || row?.id || "-"))
          )),
        ]),
      ]),
      h("div", { className: "btn-row", key: "decision_preset_pair_quick_row" }, (Array.isArray(trackCompareQuickPairOptions) ? trackCompareQuickPairOptions : []).map((row) =>
        h("button", {
          className: "btn",
          key: `decision_quick_pair_${String(row?.id || "")}`,
          onClick: () => applyTrackCompareQuickPair(row),
        }, String(row?.label || row?.id || "-"))
      )),
      h("div", { className: "hint", key: "decision_preset_pair_selected_hint" }, `selected_pair: ${String(trackCompareSelectedPairSummaryText || "-")}`),
      h("pre", { className: "result-box", key: "decision_preset_pair_forecast_box" }, String(trackCompareSelectedPairForecastText || "-")),
      h("div", { className: "btn-row", key: "decision_preset_pair_row" }, [
        h("button", {
          className: "btn",
          key: "decision_run_preset_pair_compare",
          onClick: runPresetPairTrackCompare,
        }, "Run Preset Pair Compare"),
        h("button", {
          className: "btn",
          key: "decision_run_track_compare",
          onClick: runLowVsCurrentTrackCompare,
        }, "Run Low -> Current Compare"),
      ]),
      h("div", { className: "hint", key: "decision_preset_pair_mode_hint" }, "target_preset=current_config keeps the current runtime inputs and only builds the baseline automatically."),
    ]),
    h("div", { className: "field", key: "decision_pinned_pair_quick_actions" }, [
      h("label", { className: "label", key: "decision_pinned_pair_quick_actions_label" }, "Pinned Pair Quick Actions"),
      h("div", { className: "hint", key: "decision_pinned_pair_quick_actions_hint" }, String(pinnedCompareQuickActionSummaryText || "-")),
      h("pre", { className: "result-box", key: "decision_pinned_pair_quick_actions_box" }, String(pinnedCompareQuickActionDetailText || "-")),
      ...(Array.isArray(pinnedCompareQuickActionOptions) && pinnedCompareQuickActionOptions.length > 0
        ? pinnedCompareQuickActionOptions.map((row) =>
          h("div", { className: "field", key: `decision_pinned_pair_quick_action_row_${String(row?.id || row?.pairId || "")}` }, [
            h("div", { className: "btn-row", key: `decision_pinned_pair_quick_action_buttons_${String(row?.id || row?.pairId || "")}` }, [
              h("button", {
                className: "btn",
                key: `decision_apply_pinned_pair_quick_action_${String(row?.id || row?.pairId || "")}`,
                onClick: () => applyPinnedCompareQuickAction(String(row?.id || row?.pairId || "")),
              }, `Use PIN: ${String(row?.shortLabel || row?.pairLabel || row?.id || "-")}`),
              h("button", {
                className: "btn",
                key: `decision_run_pinned_pair_quick_action_${String(row?.id || row?.pairId || "")}`,
                onClick: () => runPinnedCompareQuickAction(String(row?.id || row?.pairId || "")),
              }, `Run PIN: ${String(row?.shortLabel || row?.pairLabel || row?.id || "-")}`),
              h("button", {
                className: "btn",
                key: `decision_toggle_pinned_pair_quick_action_${String(row?.id || row?.pairId || "")}`,
                onClick: () => togglePinnedCompareQuickActionExpanded(String(row?.id || row?.pairId || "")),
              }, String(expandedPinnedCompareQuickActionId || "") === String(row?.id || row?.pairId || "")
                ? `Hide PIN Details: ${String(row?.shortLabel || row?.pairLabel || row?.id || "-")}`
                : `Show PIN Details: ${String(row?.shortLabel || row?.pairLabel || row?.id || "-")}`),
            ]),
            h("div", {
              className: "chip-list",
              key: `decision_pinned_pair_quick_action_badges_${String(row?.id || row?.pairId || "")}`,
              style: { marginBottom: "6px" },
            }, (Array.isArray(row?.quickActionBadges) && row.quickActionBadges.length > 0
              ? row.quickActionBadges
              : [{ label: "assessment:unknown", tone: "status-neutral" }]
            ).map((badge, badgeIdx) =>
              h("span", {
                className: `chip ${String(badge?.tone || "status-neutral")}`,
                key: `decision_pinned_pair_quick_action_badge_${String(row?.id || row?.pairId || "")}_${badgeIdx}`,
              }, String(badge?.label || "-"))
            )),
            h("div", { className: "hint", key: `decision_pinned_pair_quick_action_summary_${String(row?.id || row?.pairId || "")}` }, `artifact_expectation: ${String(row?.artifactExpectationSummaryText || "-")}`),
            h("div", { className: "hint", key: `decision_pinned_pair_quick_action_paths_${String(row?.id || row?.pairId || "")}` }, `artifact_path_hashes: ${String(row?.artifactPathFingerprintSummaryText || "-")}`),
            String(expandedPinnedCompareQuickActionId || "") === String(row?.id || row?.pairId || "")
              ? h("div", { className: "field", key: `decision_pinned_pair_quick_action_detail_${String(row?.id || row?.pairId || "")}` }, [
                h("pre", { className: "result-box", key: `decision_pinned_pair_quick_action_preview_${String(row?.id || row?.pairId || "")}` }, String(row?.previewText || "-")),
                h("pre", { className: "result-box", key: `decision_pinned_pair_quick_action_artifact_${String(row?.id || row?.pairId || "")}` }, String(row?.artifactExpectationDetailText || "-")),
              ])
              : null,
          ])
        )
        : [
          h("div", { className: "hint", key: "decision_pinned_pair_quick_actions_empty_hint" }, "Pin a selected history pair below to promote it here."),
        ]),
    ]),
    h("div", { className: "field", key: "decision_compare_session_history" }, [
      h("label", { className: "label", key: "decision_compare_session_history_label" }, "Compare Session History"),
      h("div", { className: "hint", key: "decision_compare_session_history_replay_hint" }, String(latestReplayableCompareSessionText || "-")),
      h("div", { className: "hint", key: "decision_compare_session_history_selected_hint" }, String(selectedReplayableCompareSessionText || "-")),
      h("div", { className: "hint", key: "decision_compare_session_history_meta_hint" }, String(selectedReplayableCompareSessionMetaText || "-")),
      h("pre", { className: "result-box", key: "decision_compare_session_history_selected_retention_box" }, String(selectedReplayableCompareSessionRetentionText || "-")),
      h("div", { className: "hint", key: "decision_compare_session_history_retention_hint" }, String(compareSessionRetentionPolicySummaryText || "-")),
      h("div", { className: "hint", key: "decision_compare_session_history_retention_group_hint" }, String(compareSessionRetentionGroupHintText || "-")),
      h("pre", { className: "result-box", key: "decision_compare_session_history_retention_preview_box" }, String(compareSessionRetentionPreviewText || "-")),
      h("div", { className: "hint", key: "decision_compare_session_history_transfer_compact_hint" }, String(compareSessionTransferCompactSummaryText || "-")),
      h("div", { className: "chip-list", key: "decision_compare_session_history_transfer_chips" }, (
        Array.isArray(compareSessionTransferBadgeRows) && compareSessionTransferBadgeRows.length > 0
          ? compareSessionTransferBadgeRows
          : [{ label: "transfer:idle", tone: "status-neutral" }]
      ).map((row, idx) =>
        h("span", {
          className: `chip ${String(row?.tone || "status-neutral")}`,
          key: `decision_compare_session_history_transfer_chip_${idx}`,
        }, String(row?.label || "-"))
      )),
      h("div", { className: "hint", key: "decision_compare_session_history_transfer_hint" }, String(compareSessionTransferStatusText || "-")),
      h("div", { className: "hint", key: "decision_compare_session_history_import_preview_hint" }, String(compareSessionImportPreviewSummaryText || "-")),
      h("pre", { className: "result-box", key: "decision_compare_session_history_import_preview_box" }, String(compareSessionImportPreviewText || "-")),
      h("pre", { className: "result-box", key: "decision_compare_session_history_preview_box" }, String(selectedReplayableCompareSessionPreviewText || "-")),
      h("pre", { className: "result-box", key: "decision_compare_session_history_artifact_expectation_box" }, String(selectedReplayableCompareSessionArtifactExpectationText || "-")),
      h("input", {
        key: "decision_compare_session_history_import_file",
        ref: compareSessionImportFileInputRef,
        type: "file",
        accept: ".json,application/json",
        style: { display: "none" },
        onChange: handleCompareSessionImportFileChange,
      }),
      h("select", {
        className: "select",
        value: String(compareSessionRetentionPolicy || ""),
        onChange: (e) => updateCompareSessionRetentionPolicy(String(e.target.value || "")),
      }, (Array.isArray(compareSessionRetentionPolicyOptions) ? compareSessionRetentionPolicyOptions : []).map((row) =>
        h("option", {
          key: `decision_compare_history_retention_${String(row?.id || "")}`,
          value: String(row?.id || ""),
        }, String(row?.label || row?.id || "-"))
      )),
      h("select", {
        className: "select",
        value: String(selectedCompareReplayPairId || ""),
        onChange: (e) => setSelectedCompareReplayPairId(String(e.target.value || "")),
      }, (Array.isArray(compareReplayPairOptions) && compareReplayPairOptions.length > 0
        ? replayPairOptionGroups.map((group) =>
          h("optgroup", {
            key: `decision_compare_history_pair_group_${String(group?.id || "")}`,
            label: String(group?.label || group?.id || "-"),
          }, (Array.isArray(group?.options) ? group.options : []).map((row) =>
            h("option", {
              key: `decision_compare_history_pair_${String(row?.id || "")}`,
              value: String(row?.id || ""),
            }, String(row?.label || row?.id || "-"))
          ))
        )
        : [
          h("option", { key: "decision_compare_history_pair_empty", value: "" }, "No replayable pairs yet"),
        ]
      )),
      h("input", {
        className: "input",
        value: String(selectedCompareReplayPairLabelDraft || ""),
        onChange: (e) => setSelectedCompareReplayPairLabelDraft(String(e.target.value || "")),
        placeholder: "selected pair label",
      }),
      h("div", { className: "btn-row", key: "decision_compare_session_history_actions" }, [
        h("button", {
          className: "btn",
          key: "decision_apply_latest_history_pair",
          onClick: applyLatestCompareSessionPair,
          disabled: !canReplayLatestCompareSession,
        }, "Use Latest History Pair"),
        h("button", {
          className: "btn",
          key: "decision_run_latest_history_pair",
          onClick: runLatestCompareSessionPair,
          disabled: !canReplayLatestCompareSession,
        }, "Run Latest History Pair"),
        h("button", {
          className: "btn",
          key: "decision_apply_selected_history_pair",
          onClick: applySelectedCompareSessionPair,
          disabled: !canReplaySelectedCompareSession,
        }, "Use Selected History Pair"),
        h("button", {
          className: "btn",
          key: "decision_run_selected_history_pair",
          onClick: runSelectedCompareSessionPair,
          disabled: !canReplaySelectedCompareSession,
        }, "Run Selected History Pair"),
      ]),
      h("div", { className: "btn-row", key: "decision_compare_session_history_manage_row" }, [
        h("button", {
          className: "btn",
          key: "decision_save_selected_history_pair_label",
          onClick: saveSelectedCompareSessionPairLabel,
          disabled: !canReplaySelectedCompareSession,
        }, "Save Selected Label"),
        h("button", {
          className: "btn",
          key: "decision_pin_selected_history_pair",
          onClick: togglePinSelectedCompareSessionPair,
          disabled: !canReplaySelectedCompareSession,
        }, "Pin Selected History Pair"),
        h("button", {
          className: "btn",
          key: "decision_delete_selected_history_pair",
          onClick: deleteSelectedCompareSessionPair,
          disabled: !canReplaySelectedCompareSession,
        }, "Delete Selected History Pair"),
        h("button", {
          className: "btn",
          key: "decision_clear_all_compare_history",
          onClick: clearAllCompareSessionHistory,
        }, "Clear All History"),
      ]),
      h("div", { className: "btn-row", key: "decision_compare_session_history_transfer_row" }, [
        h("button", {
          className: "btn",
          key: "decision_export_compare_history",
          onClick: exportCompareSessionHistory,
        }, "Export History"),
        h("button", {
          className: "btn",
          key: "decision_import_compare_history",
          onClick: triggerCompareSessionImportFilePick,
        }, "Import History"),
      ]),
      h("div", { className: "btn-row", key: "decision_compare_session_history_transfer_apply_row" }, [
        h("button", {
          className: "btn",
          key: "decision_apply_compare_history_import_preview",
          onClick: applyCompareSessionImportPreview,
          disabled: !hasCompareSessionImportPreview,
        }, "Apply Import Merge"),
        h("button", {
          className: "btn",
          key: "decision_clear_compare_history_import_preview",
          onClick: clearCompareSessionImportPreview,
          disabled: !hasCompareSessionImportPreview,
        }, "Clear Import Preview"),
      ]),
      h("pre", { className: "result-box", key: "decision_compare_session_history_box" }, String(compareSessionHistoryText || "-")),
    ]),
    h("div", { className: "btn-row", key: "decision_gate_row" }, [
      h("button", {
        className: "btn",
        key: "decision_pin_baseline",
        onClick: pinBaselineFromGraphRun,
      }, "Pin Baseline"),
      h("button", {
        className: "btn",
        key: "decision_policy_gate",
        onClick: runPolicyGateForGraphRun,
      }, "Policy Gate"),
    ]),
    h("div", { className: "btn-row", key: "decision_session_row" }, [
      h("button", {
        className: "btn",
        key: "decision_run_session",
        onClick: runDecisionRegressionSession,
      }, "Run Session"),
      h("button", {
        className: "btn",
        key: "decision_export_session",
        onClick: exportDecisionRegressionSession,
      }, "Export Session"),
    ]),
    h("div", { className: "btn-row", key: "decision_export_row" }, [
      h("button", {
        className: "btn",
        key: "decision_export_gate",
        onClick: exportGateReport,
      }, "Export Gate"),
      h("button", {
        className: "btn",
        key: "decision_export_brief",
        onClick: exportDecisionBriefMd,
      }, "Export Brief"),
    ]),
    h("pre", { className: "result-box", key: "decision_summary_box" }, String(decisionSummaryText || "-")),
    h("div", { className: "hint", key: "decision_status_hint" }, `decision_ops: ${String(decisionOpsStatusText || "-")}`),
    h("div", { className: "hint", key: "track_compare_status_hint" }, `track_compare_status: ${String(trackCompareRunnerStatusText || "-")}`),
    h("div", { className: "hint", key: "compare_status_hint" }, `compare_status: ${String(compareRunStatusText || "-")}`),
    h("div", { className: "hint", key: "session_status_hint" }, [
      `session_id=${String(lastRegressionSession?.session_id || "-")} | `,
      `export_id=${String(lastRegressionExport?.export_id || "-")}`,
    ]),
  ]);
}
