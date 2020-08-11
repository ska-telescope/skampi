{{range .items}}
    {{ .metadata.name}}
    {{- range $key, $value := .metadata.labels}}
        {{ $key}}: {{$value}}
    {{- end}}
{{- end}}