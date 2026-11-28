import logging

logger = logging.getLogger("agent_memory_lite")


def setup_logging(debug: bool = False) -> None:
    """初始化日志配置，仅对本项目包开启 DEBUG 以避免第三方库刷屏"""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
