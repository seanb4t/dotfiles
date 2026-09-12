{{/* chezmoi:modify-template */ -}}
{{- $existing := .chezmoi.stdin -}}
{{- /* Only replace the exact legacy snapshot; preserve any personal edits. */ -}}
{{- if eq (sha256sum $existing) "de0bc388a5b3ff83d7c28dfee891ce8752d168b57db6a3144f9553ffdb550a77" -}}
{{- $existing = "" -}}
{{- end -}}
{{- $existing = regexReplaceAll "(?s)<!-- chezmoi:user-preferences:start -->.*?<!-- chezmoi:user-preferences:end -->" $existing "" -}}
{{- $existing = regexReplaceAll "(?s)<!-- chezmoi:claude-guidance:start -->.*?<!-- chezmoi:claude-guidance:end -->" $existing "" -}}
{{- $existing = replace (include ".chezmoitemplates/claude-guidance.md") "" $existing | trim -}}
{{ includeTemplate "user-preferences.md.tmpl" . }}

<!-- chezmoi:claude-guidance:start -->
{{ include ".chezmoitemplates/claude-guidance.md" }}
<!-- chezmoi:claude-guidance:end -->
{{ if $existing }}
{{ $existing }}
{{ end -}}
