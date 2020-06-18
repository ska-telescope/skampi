{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "sdp-prototype.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "sdp-prototype.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "sdp-prototype.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "sdp-prototype.labels" -}}
app.kubernetes.io/name: {{ include "sdp-prototype.name" . }}
helm.sh/chart: {{ include "sdp-prototype.chart" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Init container to wait for configuration database availability */}}
{{- define "sdp-prototype.etcd-host" -}}
{{ include "sdp-prototype.fullname" . }}-etcd-client.{{ .Release.Namespace }}.svc.cluster.local
{{- end -}}
{{- define "sdp-prototype.wait-for-etcd" -}}
- image: quay.io/coreos/etcd:v{{ .Values.etcd.version }}
  name: {{ .Chart.Name }}-wait-for-etcd
  command: ["/bin/sh", "-c", "while ( ! etcdctl endpoint health ); do sleep 1; done"]
  env:
  - name: ETCDCTL_ENDPOINTS
    value: "http://{{ include "sdp-prototype.etcd-host" . }}:2379"
  - name: ETCDCTL_API
    value: "3"
{{- end -}}
