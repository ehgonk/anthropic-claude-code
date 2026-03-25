interface ViaCepResponse {
  cep: string
  logradouro: string
  complemento: string
  bairro: string
  localidade: string
  uf: string
  ibge: string
  erro?: boolean
}

export async function lookupCep(cep: string): Promise<ViaCepResponse | null> {
  const cleanCep = cep.replace(/\D/g, "")
  if (cleanCep.length !== 8) return null

  const response = await fetch(`https://viacep.com.br/ws/${cleanCep}/json/`)
  if (!response.ok) return null

  const data = (await response.json()) as ViaCepResponse
  if (data.erro) return null

  return data
}
