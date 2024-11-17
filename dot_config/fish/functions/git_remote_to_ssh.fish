
function git_remote_to_ssh --description "Change the remote URL from HTTPS to SSH"
    # Define the remote name (usually 'origin') by default unless an argument is provided
    set remote_name $argv[1]
    if test -z $remote_name
        set remote_name "origin"
    end
    
    # Get the current remote URL
    set current_url (git remote get-url $remote_name)

    # Check if the current URL is HTTPS
    if string match -q "https://*" $current_url
        # Replace 'https://' with 'git@' and '.com/' with '.com:'
        set ssh_url (string replace "https://" "git@" $current_url)
        set ssh_url (string replace ".com/" ".com:" $ssh_url)

        # Set the new SSH URL as the remote URL
        git remote set-url $remote_name $ssh_url

        echo "Changed remote URL from HTTPS to SSH:"
        echo $ssh_url
    else
        echo "The current remote URL is not an HTTPS URL."
    end
end
