from .interface import EntryPoint
from src.common.workers_pool import WorkersPool
from src.common.document_type import DocumentType
from src.rag_pipelines import RagPipeline

import tempfile
from argparse import ArgumentParser, Namespace
import logging
from pathlib import Path
import shutil
import time
import asyncio

import gradio as gr
from uvicorn import Config, Server
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

FILES_MOUNT_POINT = Path("/files")

FASTAPI_APP = FastAPI(
    allow_origins=["*"],
)


class GradioEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._share_link = args.share
        self._files_uploading_semaphore = asyncio.Semaphore(
            self._config["server"].pop("n_of_file_uploading_in_parallel", 2)
        )
        self._rag = RagPipeline.create(
            self._config["rag"].pop("type"),
            config=self._config,
        )

        self._files_storage = Path(self._config["server"].pop("files_storage_path"))
        self._server_config = Config(
            FASTAPI_APP,
            **self._config["server"],
        )

        self._files_storage.mkdir(parents=True, exist_ok=True)
        FASTAPI_APP.mount(
            str(FILES_MOUNT_POINT),
            StaticFiles(directory=self._files_storage),
            name="raw_files",
        )

        self.configure_fast_api()

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("--share", action="store_true", default=False)

    async def api_rag_pipeline(self, params: dict):
        query: str = params["query"]
        async with asyncio.TaskGroup() as tg:
            chunks = tg.create_task(self.api_rag_chunks(params))
            response = tg.create_task(self._rag.search(query, list()))

        return {
            "response": await response,
            "retrieved_chunks": await chunks,
        }

    async def api_rag_chunks(self, params: dict):
        query: str = params["query"]
        n_of_chunks: int = params.get("n_of_chunks", 10)
        records = await self._rag.retrieve_docs(query, n_of_chunks)

        return [{"score": score, "record": record} for score, record in records]

    def configure_fast_api(self):
        FASTAPI_APP.get("/api/rag_pipeline")(self.api_rag_pipeline)
        FASTAPI_APP.get("/api/rag_chunks")(self.api_rag_chunks)

    async def respond(self, message, chat_history):
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": ""})
        yield "", chat_history

        response = await self._rag.search(message, chat_history)
        chat_history[-1]["content"] = response.response
        yield "", chat_history

        if response.references:
            chat_history.append({"role": "assistant", "content": "\n## References:\n"})
        for i in set(response.references):
            chat_history.append(
                {
                    "role": "assistant",
                    "content": f"- [{i.name}]({FILES_MOUNT_POINT / i.name})",
                }
            )

        yield "", chat_history

    async def upload_file(self, files):
        async with asyncio.TaskGroup() as gr:
            for file in files:
                gr.create_task(self.upload_file_impl(file))

        yield ""

    async def upload_file_impl(self, file: tempfile._TemporaryFileWrapper):
        async with self._files_uploading_semaphore:
            logger.info(f"Uploaded file stored in: {file}")
            stored_path = self._files_storage / Path(file.name).name
            logger.info(f"Got stored path: {stored_path}")

            file_name_for_logger = Path(file.name).name
            begin = time.time()
            if stored_path.exists():
                gr.Warning(
                    f"{file_name_for_logger} already added.\nIt will be deleted, then uploaded again.",
                    duration=3,
                )
                await self._rag.delete_document(stored_path)

            await asyncio.to_thread(shutil.copy, file.name, stored_path)
            await self._rag.add_document(stored_path)
            end = time.time()

            mcs_took = float(int((end - begin) * 10e5))

            gr.Info(
                f"{file_name_for_logger} uploaded sucessfully in {mcs_took / 1000} ms",
                duration=5,
            )

    def configure_gradio(self) -> gr.Blocks:
        with gr.Blocks(fill_height=True) as demo:
            gr.Label("Perovskite rag modeller", scale=1)
            chatbot = gr.Chatbot(scale=10)
            with gr.Row():
                txt_box = gr.Textbox(
                    show_label=False,
                    placeholder="Введите сообщение и нажмите Enter",
                    scale=5,
                )
                with gr.Column(scale=1):
                    send_button = gr.Button("Send")
                    clear_button = gr.Button("Clear")
                    send_button.click(
                        self.respond,
                        inputs=[txt_box, chatbot],
                        outputs=[txt_box, chatbot],
                    )
                    clear_button.click(
                        lambda: ("", {}), inputs=[], outputs=[txt_box, chatbot]
                    )

                txt_box.submit(
                    self.respond, inputs=[txt_box, chatbot], outputs=[txt_box, chatbot]
                )
            upload_button = gr.UploadButton(
                "Upload file",
                file_types=[f".{i.name}" for i in DocumentType],
                file_count="multiple",
            )

            hidden_txt = gr.Textbox(visible=False)
            upload_button.upload(
                fn=self.upload_file,
                inputs=[upload_button],
                outputs=[hidden_txt],
            )

        return demo

    async def _run_impl(self) -> None:
        logger.debug("entery_point started")
        blocks = self.configure_gradio()
        gr.mount_gradio_app(FASTAPI_APP, blocks, path="/")

        server = Server(self._server_config)
        await server.serve()

    async def run(self) -> None:
        n_of_workers = self._config.get("common", {}).get("n_of_workers")
        if n_of_workers:
            async with await WorkersPool.create_pool(n_of_workers):
                return await self._run_impl()
        return await self._run_impl()
