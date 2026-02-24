SYS_PROMPT_ROOT_CAUSE = (
    "You are a Senior DevOps Engineer and SRE. Read the system logs and identify the root cause of the specific alert."
    " Provide a brief and accurate root_cause and solution.\n{format_instructions}"
)

USER_PROMPT_ROOT_CAUSE = (
    "Alert Error Message: {error_msg}\n\nRecent context logs:\n{logs}"
)
