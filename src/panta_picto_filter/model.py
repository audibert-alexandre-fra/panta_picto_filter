from prompt import PROMPT, PROMPT_CLASSIFICATION, PROMPT_FILTER_TEXT_PICTO
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer


class LlmAsJudge:
    """Wrapper around a vLLM model used as an LLM-as-judge.

    Supports three tasks: ``"filter_text"``, ``"classification"``
    and ``"filter_text_picto"``.

    Args:
        name_model: HuggingFace model identifier.
        temperature: Sampling temperature.
        top_p: Top-p (nucleus) sampling parameter.
        top_k: Top-k sampling parameter. -1 disables filtering.
        max_tokens: Maximum number of generated tokens.
        task: One of ``"filter_text"``, ``"classification"``,
            ``"filter_text_picto"``.
    """

    def __init__(
        self,
        name_model: str = "Qwen/Qwen3-8B",
        temperature: float = 0,
        top_p: float = 1,
        top_k: float = -1,
        max_tokens: int = 100,
        max_model_len: int = 4096,
        gpu_memory_utilization: float = 0.9,
        task: str = "filter_text",
    ) -> None:
        self.model_name: str = name_model
        self.tokenizer = AutoTokenizer.from_pretrained(name_model)
        self.llm = LLM(
            model=name_model,
            max_model_len=max_model_len,
            gpu_memory_utilization=gpu_memory_utilization,
        )
        self.sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens,
        )
        self.task: str = task

    def text_process(self, text: str) -> str:
        """Apply the chat template for the configured task.

        Args:
            text: User message content.

        Returns:
            The formatted prompt string ready for generation.

        Raises:
            ValueError: If the task is not recognised.
        """
        match self.task:
            case "filter_text":
                system_prompt = PROMPT
            case "classification":
                system_prompt = PROMPT_CLASSIFICATION
            case "filter_text_picto":
                system_prompt = PROMPT_FILTER_TEXT_PICTO
            case _:
                raise ValueError(f"Tâche inconnue : {self.task}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]

        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

    def process_texts(self, texts: list[str]) -> list[str]:
        """Generate completions for a list of texts.

        Args:
            texts: List of raw user messages to process.

        Returns:
            List of generated output strings, one per input text.
        """
        processed_texts = [self.text_process(t) for t in texts]
        outputs = self.llm.generate(processed_texts, self.sampling_params)
        return [o.outputs[0].text for o in outputs]
