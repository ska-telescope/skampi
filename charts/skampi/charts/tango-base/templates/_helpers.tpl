{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "tango-base.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{/*
service-name based on values in order to make it constant accross the deplpyent namespace
*/}}
{{- define "tango-base.dbservice-name" -}}
{{- if .Values.tangoDatabaseDS }}
{{- .Values.tangoDatabaseDS }}
{{- else }}
    {{- if .Values.databaseds.domainTag -}}
databaseds-{{ template "tango-base.name" . }}-{{ .Values.databaseds.domainTag }}
    {{- else -}}
databaseds-{{ template "tango-base.name" . }}-{{ .Release.Name }}
    {{- end }}
{{- end }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "tango-base.fullname" -}}
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
Common labels
*/}}
{{- define "tango-base.labels" }}
app: {{ template "tango-base.name" . }}
chart: {{ template "tango-base.chart" . }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
system: {{ .Values.system }}
telescope: {{ .Values.telescope }}
{{- end }}
{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "tango-base.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}
