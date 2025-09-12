# Finansal Okuryazarlık Botu – API Kullanım Örneği

Bu doküman, `pmpt_68c2dfa985b08190b2c9a761d46e771d00270e9029c6a158` kimlikli eğitilmiş modeli 
OpenAI Python SDK üzerinden nasıl çağırabileceğinizi göstermektedir.

---

## 🔹 Python ile Kullanım

```python
from openai import OpenAI

# İstemciyi başlat
client = OpenAI()

# Eğitilmiş modelinizi çağırma
response = client.responses.create(
    model="pmpt_68c2dfa985b08190b2c9a761d46e771d00270e9029c6a158",
    input="Bana bileşik faiz hesaplamasını basit bir örnekle açıkla."
)

print(response.output[0].content[0].text)
```

---

## 🔹 Önemli Noktalar
- `model` parametresinde kendi özel model kimliğinizi kullanıyorsunuz:  
  ```
  pmpt_68c2dfa985b08190b2c9a761d46e771d00270e9029c6a158
  ```
- `input` kısmına kullanıcı mesajını veriyorsunuz.
- Çıktıyı almak için:
  ```python
  response.output[0].content[0].text
  ```

---

## 🔹 Örnek Yanıt
Eğer `input="Bana bütçe planlaması hakkında ipucu ver."` derseniz, 
model aşağıdakine benzer eğitim amaçlı bir yanıt dönecektir:

```
Bütçe planlamasında en önemli adım gelir ve giderleri yazmaktır.
Önce sabit giderlerini (kira, fatura, ulaşım) yaz, sonra tasarruf payı ayır,
en sonunda değişken harcamaları planla.
```
