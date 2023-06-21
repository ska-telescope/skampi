from ska_control_model import ResultCode


class CommandException(Exception):
    def __init__(self, result: tuple[ResultCode, str]) -> None:
        arg = f"Command failed (code {result[0]} with message {result[1]})"
        super().__init__(arg)


def command_success(result: tuple[list[ResultCode], list[str]]):
    command_status = result[0][0]
    return command_status in [
        ResultCode.ABORTED,
        ResultCode.OK,
        ResultCode.QUEUED,
        ResultCode.STARTED,
    ]
