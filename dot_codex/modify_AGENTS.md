{{/* chezmoi:modify-template */ -}}
{{- $existing := regexReplaceAll "(?s)<!-- chezmoi:user-preferences:start -->.*?<!-- chezmoi:user-preferences:end -->" .chezmoi.stdin "" | trim -}}
{{ includeTemplate "user-preferences.md.tmpl" . }}
{{ if $existing }}
{{ $existing }}
{{ end -}}
