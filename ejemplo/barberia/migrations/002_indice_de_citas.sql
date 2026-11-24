-- Acelera la revisión de cruces y la agenda: siempre se busca por barbero y por hora de inicio.
CREATE INDEX IF NOT EXISTS idx_citas_barbero_inicio ON citas (barbero_id, inicio);
