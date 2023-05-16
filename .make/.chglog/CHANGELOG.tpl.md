{{ range .Versions -}}
## {{ if .Tag.Previous }}[{{ .Tag.Name }}]{{ else }}{{ .Tag.Name }}{{ end }}
{{ $jiraList := list }}
### Jira Tickets
{{ if .CommitGroups -}}
{{ range .CommitGroups -}}
{{ range .Commits -}}
{{ if .JiraIssue -}}{{ if not (has .JiraIssueID $jiraList) -}}
{{ $jiraList = append $jiraList .JiraIssueID -}}
- {{ .JiraIssueID }} - {{ .JiraIssue.Summary }}
{{ end -}}{{ end -}}
{{ end }}
{{ end -}}
{{ else }}
{{ range .Commits -}}
{{ if .JiraIssue -}}{{ if not (has .JiraIssueID $jiraList) -}}
{{ $jiraList = append $jiraList .JiraIssueID -}}
- {{ .JiraIssueID }} - {{ .JiraIssue.Summary }}
{{ end -}}{{ end -}}
{{ end -}}
{{ end }}

### Commits
{{ if .CommitGroups -}}
{{ range .CommitGroups -}}
{{ range .Commits -}}
{{ if .JiraIssueID -}}
- {{ .JiraIssueID }}: {{ .Subject }}
{{ else -}}
- {{ .Header }}
{{ end -}}
{{ end }}
{{ end -}}
{{ else }}
{{ range .Commits -}}
{{ if .JiraIssueID -}}
- {{ .JiraIssueID }}: {{ .Subject }}
{{ else -}}
- {{ .Header }}
{{ end -}}
{{ end }}
{{ end -}}

{{- if .RevertCommits -}}
### Reverts
{{ range .RevertCommits -}}
- {{ .Revert.Header }}
{{ end }}
{{ end -}}
{{ end }}

{{- if .Versions }}
{{ range .Versions -}}
{{ if .Tag.Previous -}}
\[{{ .Tag.Name }}\]: {{ $.Info.RepositoryURL }}/compare/{{ .Tag.Previous.Name }}...{{ .Tag.Name }}

[{{ .Tag.Name }}]: {{ $.Info.RepositoryURL }}/compare/{{ .Tag.Previous.Name }}...{{ .Tag.Name }}
{{ end -}}
{{ end -}}
{{ end -}}
