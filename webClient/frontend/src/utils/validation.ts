// Frontend input validation utilities for WaddlePerf webClient

export interface ValidationResult {
  valid: boolean
  error?: string
}

// Security constants
export const MAX_TARGET_LENGTH = 255
export const MAX_QUERY_LENGTH = 255
export const MAX_TIMEOUT_SECONDS = 300
export const MAX_COUNT = 1000
export const MIN_PORT = 1
export const MAX_PORT = 65535

// Valid protocol values (whitelist)
const VALID_HTTP_PROTOCOLS = new Set([
  'http1', 'http/1.1', 'http1.1', 'http2', 'http/2', 'http3', 'http/3',
  'HTTP/1.1', 'HTTP/2', 'HTTP/3'
])

const VALID_TCP_PROTOCOLS = new Set([
  'raw', 'raw_tcp', 'Raw TCP', 'tcp', 'tls', 'TLS', 'ssh', 'SSH'
])

const VALID_UDP_PROTOCOLS = new Set([
  'dns', 'DNS', 'raw', 'raw_udp', 'Raw UDP', 'udp'
])

const VALID_ICMP_PROTOCOLS = new Set(['ping', 'traceroute'])

// Regex patterns for validation
const HOSTNAME_REGEX = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/
const DOMAIN_REGEX = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.?$/
const IP_REGEX = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/

/**
 * Validate a target hostname or IP address
 */
export function validateTarget(target: string): ValidationResult {
  if (!target || target.trim() === '') {
    return { valid: false, error: 'Target cannot be empty' }
  }

  if (target.length > MAX_TARGET_LENGTH) {
    return { valid: false, error: `Target exceeds maximum length of ${MAX_TARGET_LENGTH}` }
  }

  // Remove URL scheme if present
  let cleanTarget = target
  if (target.includes('://')) {
    try {
      const url = new URL(target)
      cleanTarget = url.hostname
    } catch {
      return { valid: false, error: 'Invalid URL format' }
    }
  }

  // Remove port if present
  let host = cleanTarget
  if (cleanTarget.includes(':')) {
    const parts = cleanTarget.split(':')
    host = parts[0]
  }

  // Check if it's a valid IP address
  if (IP_REGEX.test(host)) {
    return { valid: true }
  }

  // Check if it's a valid hostname
  if (!HOSTNAME_REGEX.test(host)) {
    return { valid: false, error: 'Invalid hostname format' }
  }

  // Basic SSRF protection: warn about localhost/internal IPs
  const lowerHost = host.toLowerCase()
  if (
    lowerHost === 'localhost' ||
    lowerHost === '0.0.0.0' ||
    host.startsWith('127.') ||
    host.startsWith('169.254.') ||
    host.startsWith('10.') ||
    host.startsWith('192.168.')
  ) {
    // We'll allow it but could add a warning in UI
  }

  return { valid: true }
}

/**
 * Validate a DNS query string
 */
export function validateDNSQuery(query: string): ValidationResult {
  if (!query || query.trim() === '') {
    return { valid: false, error: 'DNS query cannot be empty' }
  }

  if (query.length > MAX_QUERY_LENGTH) {
    return { valid: false, error: `Query exceeds maximum length of ${MAX_QUERY_LENGTH}` }
  }

  if (!DOMAIN_REGEX.test(query)) {
    return { valid: false, error: 'Invalid domain name format' }
  }

  return { valid: true }
}

/**
 * Validate a port number
 */
export function validatePort(port: number | string): ValidationResult {
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port

  if (isNaN(portNum)) {
    return { valid: false, error: 'Port must be a number' }
  }

  if (portNum < MIN_PORT || portNum > MAX_PORT) {
    return { valid: false, error: `Port must be between ${MIN_PORT} and ${MAX_PORT}` }
  }

  return { valid: true }
}

/**
 * Validate a timeout value
 */
export function validateTimeout(timeout: number | string): ValidationResult {
  const timeoutNum = typeof timeout === 'string' ? parseInt(timeout, 10) : timeout

  if (isNaN(timeoutNum)) {
    return { valid: false, error: 'Timeout must be a number' }
  }

  if (timeoutNum < 1) {
    return { valid: false, error: 'Timeout must be at least 1 second' }
  }

  if (timeoutNum > MAX_TIMEOUT_SECONDS) {
    return { valid: false, error: `Timeout cannot exceed ${MAX_TIMEOUT_SECONDS} seconds` }
  }

  return { valid: true }
}

/**
 * Validate a count/iteration value
 */
export function validateCount(count: number | string): ValidationResult {
  const countNum = typeof count === 'string' ? parseInt(count, 10) : count

  if (isNaN(countNum)) {
    return { valid: false, error: 'Count must be a number' }
  }

  if (countNum < 1) {
    return { valid: false, error: 'Count must be at least 1' }
  }

  if (countNum > MAX_COUNT) {
    return { valid: false, error: `Count cannot exceed ${MAX_COUNT}` }
  }

  return { valid: true }
}

/**
 * Validate HTTP protocol
 */
export function validateHTTPProtocol(protocol: string): ValidationResult {
  if (!protocol || protocol.trim() === '') {
    return { valid: true } // Will use default
  }

  if (!VALID_HTTP_PROTOCOLS.has(protocol)) {
    return { valid: false, error: 'Invalid HTTP protocol' }
  }

  return { valid: true }
}

/**
 * Validate TCP protocol
 */
export function validateTCPProtocol(protocol: string): ValidationResult {
  if (!protocol || protocol.trim() === '') {
    return { valid: true } // Will use default
  }

  if (!VALID_TCP_PROTOCOLS.has(protocol)) {
    return { valid: false, error: 'Invalid TCP protocol' }
  }

  return { valid: true }
}

/**
 * Validate UDP protocol
 */
export function validateUDPProtocol(protocol: string): ValidationResult {
  if (!protocol || protocol.trim() === '') {
    return { valid: true } // Will use default
  }

  if (!VALID_UDP_PROTOCOLS.has(protocol)) {
    return { valid: false, error: 'Invalid UDP protocol' }
  }

  return { valid: true }
}

/**
 * Validate ICMP protocol
 */
export function validateICMPProtocol(protocol: string): ValidationResult {
  if (!protocol || protocol.trim() === '') {
    return { valid: true } // Will use default
  }

  if (!VALID_ICMP_PROTOCOLS.has(protocol)) {
    return { valid: false, error: 'Invalid ICMP protocol' }
  }

  return { valid: true }
}

/**
 * Sanitize a string by removing control characters
 */
export function sanitizeString(input: string, maxLength: number): string {
  // Trim whitespace
  let s = input.trim()

  // Limit length
  if (s.length > maxLength) {
    s = s.substring(0, maxLength)
  }

  // Remove control characters except tab, newline, carriage return
  s = s.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')

  return s
}
