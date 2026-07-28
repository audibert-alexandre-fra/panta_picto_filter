from prompt import PROMPT, PROMPT_CLASSIFICATION, PROMPT_FILTER_TEXT_PICTO
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer


class LlmAsJudge:
    def __init__(
        self,
        name_model: str = "Qwen/Qwen3-8B",
        temperature: float = 0,
        top_p: float = 1,
        top_k: float = -1,
        max_tokens: int = 100,
        task: bool = False
    ) -> None:

        self.model_name = name_model

        self.tokenizer = AutoTokenizer.from_pretrained(name_model)

        self.llm = LLM(model=name_model)

        self.sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens
        )
        self.task = task

    def text_process(self, text: str) -> str:
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
            {"role": "user", "content": text}
        ]

        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

    def process_texts(self, texts: list[str]) -> list[str]:

        processed_texts = [
            self.text_process(t) for t in texts
        ]

        outputs = self.llm.generate(
            processed_texts,
            self.sampling_params
        )

        return [o.outputs[0].text for o in outputs]