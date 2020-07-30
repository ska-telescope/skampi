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
{{- define "sdp-prototype.labels" }}
app: {{ template "sdp-prototype.name" . }}
chart: {{ template "sdp-prototype.chart" . }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
system: {{ .Values.system }}
telescope: {{ .Values.telescope }}
{{- end }}

{{/* Init container to wait for configuration database availability */}}
{{- define "sdp-prototype.etcd-host" -}}
{{ include "sdp-prototype.name" . }}-etcd-client.{{ .Release.Namespace }}.svc.cluster.local
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

{{/* for populating env variables based on the presence of env names for
item */}}
{{- define "sdp-proto.get_env"}}
{{- if index .global.Values "feature" "config-db" }}
  {{- if hasKey .deviceserver.env "TOGGLE_CONFIG_DB" }}
- name: TOGGLE_CONFIG_DB
  value: {{ quote (index .global.Values "feature" "config-db") }}
- name: SDP_CONFIG_HOST
  value: {{ include "sdp-prototype.etcd-host" .global }}
  {{- end }}
{{- end}}
{{- if hasKey .deviceserver.env "TOGGLE_AUTO_REGISTER" }}
- name: TOGGLE_AUTO_REGISTER
  value: "0"
{{- end }}
{{- if hasKey .deviceserver.env "TOGGLE_RECEIVE_ADDRESSES_HACK" }}
- name: TOGGLE_RECEIVE_ADDRESSES_HACK
  value: {{ quote (index .global.Values "feature" "receive-addresses-hack") }}
{{- end }}
{{- end}}