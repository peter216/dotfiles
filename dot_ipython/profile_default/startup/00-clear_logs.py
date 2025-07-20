import logging
import sys


## Clears handlers from the root logger and all other existing loggers.
def clear_all_logging_handlers():
    ## Get the root logger
    root_logger = logging.getLogger()
    ## Remove all handlers from the root logger
    ## Iterate over a copy of the list to avoid modification issues
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        ## Close the handler to release resources
        handler.close()

    ## Iterate through all known loggers managed by the logging framework
    ## loggerDict contains logger instances (and placeholders)
    for name, logger in logging.Logger.manager.loggerDict.items():
        ## Check if it's a Logger instance (not a placeholder)
        if isinstance(logger, logging.Logger):
            ## Remove all handlers from this specific logger
            ## Iterate over a copy of the list
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                ## Close the handler
                handler.close()


from IPython.core.magic import register_line_magic


## Defines the IPython line magic %clear_logs
@register_line_magic
def clear_logs(line):
    ## Call the function to remove all handlers
    clear_all_logging_handlers()
    print("All logging handlers removed.")
