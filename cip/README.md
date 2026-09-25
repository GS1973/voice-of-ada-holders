---
CIP: "?"
Title: Holder Answers on Governance Actions
Category: Metadata
Status: Proposed
Authors:
    - Smit Blockchain Operations (Pool BKIND) <developmentbkind@gmail.com>
Implementors:
    - The Voice of ADA Holders <https://voiceofadaholders.com>
Discussions:
    - Original PR: https://github.com/cardano-foundation/CIPs/pull/1277
Created: 2026-09-24
License: CC-BY-4.0
---

## Abstract

This CIP defines a transaction metadata record with which an ADA holder answers
Yes, No or Abstain on one or more governance actions, signed with the holder's
stake key. There is no survey to publish and no owner: every governance action
on chain is a question by itself, from the moment it is submitted until the
ledger stops accepting votes on it. The records are public, and anyone can
recount them from the chain with the rules in this document.

## Motivation: Why is this CIP necessary?

In Cardano governance the vote belongs to DReps, stake pool operators and the
Constitutional Committee, and DRep and SPO votes are weighted by stake. What
holders themselves think about an action, counted as people, is not recorded
anywhere. A holder who disagrees with their DRep has no way to say so on chain
short of changing their delegation.

Existing survey formats, such as CIP-179, link answers to a survey that someone
must first publish, with an owner who can cancel it. In CIP-179 a survey is
linked to a governance action only if the action's own anchor document names
it, so only the proposer can make that link, and only at submission. Holder
opinion on an action whose proposer did not link a survey can only be gathered
in a standalone survey, published by someone who chooses which actions get
one. This CIP removes that step: an answer refers directly to the governance
action ID the ledger assigned, so the agenda is exactly the set of actions on
chain.

## Specification

The key words MUST, MUST NOT, SHOULD and MAY are to be interpreted as described
in RFC 2119.

### Metadata label

Records use transaction metadata label `1695`, to be registered in CIP-10. The number is next to `1694`, the
label of CIP-1694, the governance these answers are about; on 2026-09-24 it was
neither registered nor used on mainnet.

### Record

A transaction carries at most one record, the value under the label:

```cddl
record = {
  0 => 1,                       ; format version
  1 => credential,              ; the answering stake credential
  2 => [+ answer],              ; one or more answers
  * uint => any                 ; later optional fields; readers ignore them
}

credential    = [0, bytes .size 28]          ; stake key hash
answer        = [gov_action_id, choice]
gov_action_id = [bytes .size 32, uint .size 2]   ; transaction hash, index
choice        = 0 / 1 / 2                    ; 0 = No, 1 = Yes, 2 = Abstain
```

The record is an integer-keyed map, as the ledger's `transaction_body`.
Encoders MUST emit the keys in ascending numeric order, without duplicates
(RFC 8949 §4.2). Readers MUST ignore keys they do not know: later revisions may
add optional fields at new keys without changing the version. The version
changes only for a change that existing readers would misread.

The credential encoding and the choice values are those of the ledger (Conway
CDDL), so that a tool can compare an answer with official votes without a
translation table. Credential tag `1` (script hash) is reserved; version 1
accepts key hashes only.

Example, in the JSON form of the detailed metadata schema: Yes on one
mainnet action and No on another, by an illustrative (not real) key hash:

```json
{ "1695": { "map": [
  { "k": { "int": 0 }, "v": { "int": 1 } },
  { "k": { "int": 1 }, "v": { "list": [
      { "int": 0 },
      { "bytes": "1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5" } ] } },
  { "k": { "int": 2 }, "v": { "list": [
      { "list": [ { "list": [
          { "bytes": "f6fd3678f12edc58dd8739560149fcdb0b8b6fc77a5f303d49c87c74d1fccb4c" },
          { "int": 0 } ] }, { "int": 1 } ] },
      { "list": [ { "list": [
          { "bytes": "75e7882a8ef2bc39517bffbfb654e89f525def5a8364d81e11fc5facafc6dd9b" },
          { "int": 0 } ] }, { "int": 0 } ] } ] } }
] } }
```

### Proof of the answerer

The key hash in the credential (key `1`) MUST be listed in the transaction's `required_signers`
(transaction body field 14). The ledger then only accepts the transaction if it
carries a valid signature by that key, so a record naming a credential it was
not signed by cannot reach the chain.

A record in a transaction that failed phase-2 validation (`is_valid = false`)
MUST be ignored.

### Validity of a record

A record MUST be ignored as a whole if any of the following holds:

- the label value is not a map, or lacks key `0`, `1` or `2`;
- the version (key `0`) is not `1`;
- the credential or any answer does not match the CDDL above;
- the key hash in the credential is not in the transaction's
  `required_signers`.

Tools MUST ignore records with a version they do not know. Unknown keys are
not a reason to ignore a record.

### Validity of an answer

An answer in a valid record counts only if all of the following hold:

1. **The action exists.** `gov_action_id` identifies a governance action
   submitted on chain before the transaction carrying the answer.
2. **The answer is on time.** The block carrying the answer lies before the
   action's closing time: the start of the first epoch in which the ledger
   accepts no more votes on the action by DReps, SPOs and the Constitutional
   Committee. That is the epoch in which the action leaves the ledger's
   proposals (enacted, expired or dropped), or epoch
   `submitted + govActionLifetime + 1`, whichever comes first. An action
   ratified into that last epoch stays among the proposals until it is enacted
   an epoch later, but takes no votes in it, and no answers.
3. **The credential was there first.** The stake credential of the record was
   registered in the ledger state to which the transaction submitting the
   action was applied, and stayed registered without interruption until the
   closing time. For a tally taken while the action is still open, until the
   point of the tally.

Answers that fail these conditions are ignored individually; other answers in
the same record still count.

### Latest answer counts

For each pair of governance action and credential, only the latest answer
counts. Order is the order of the chain: block number, then the position of the
transaction in the block, then the position of the answer in the list at key `2`. A holder
changes an answer by posting a new record before the closing time.

### Requirement on wallets

To support this CIP, a wallet MUST sign a transaction with the stake key whose
hash is listed in `required_signers`, when that key belongs to the wallet. With
CIP-30 this is `signTx`.

### What this CIP does not define

- How answers are weighed or presented. A tally may count credentials, stake,
  or both; that is a choice of whoever tallies.
- Any free text or reasoning attached to an answer.
- Answers by script credentials.

## Rationale: How does this CIP achieve its goals?

**No survey, no owner.** Every governance action is a question by itself.
Nobody decides which actions holders may answer on, and nobody can withdraw a
question.

**The answering window of the ledger.** Holders can answer exactly while an
official vote can still be cast, and not after. A tally then describes what
holders thought while the decision was still open.

**Registered before submission.** Only credentials that existed before an action
was known can answer on it. Creating many credentials in response to a
particular action is therefore not possible, and a registered credential costs
a deposit for as long as it exists.

**Weight left out of the record.** One credential, one voice, is the natural
count of holders as people, but a large holder can split into many credentials.
Leaving weight to the tally lets a tool show the count of credentials and the
stake behind them side by side, so such splitting stays visible.

**Key credentials only.** A native-script credential could be proven as in
CIP-179, by required signers that satisfy the script, and a Plutus-script
credential only through a redeemer, which metadata does not have. A native
multisig answer needs signatures from several parties, which a single wallet
cannot collect, and no tool for this CIP would support it. On 2026-09-25,
2,093 of 1,466,142 registered stake credentials on mainnet (0.14%) were script
credentials. Version 1 leaves them out; credential tag `1` is reserved for a
later version.

**Ledger encodings.** Integer keys, the credential form, the action ID and the
choice values follow the Conway ledger CDDL, so a tool can join answers with
votes and proposals without translation. CIP-179 uses the same conventions.

**Room to grow without breaking.** Because readers ignore unknown keys, an
optional field, such as an anchor to a document giving the reason for an
answer, can be added later without a new version and without invalidating
answers already on chain. Version 1 deliberately has no such field: a count of
holders needs no reasons, and every link shown to readers is content a tool
must fetch, verify and answer for.

**Several answers per transaction.** A holder can answer on all open actions
at once for a single fee. An answer is about 40 bytes, so even a record
answering on every open action stays far within the maximum transaction size.

**Relation to CIP-179.** CIP-179 (On-Chain Surveys and Polls) is a general
survey format. This CIP follows it in three points: proof through
`required_signers`, the latest answer counting, and several answers per
transaction. It differs in referring directly to governance actions instead of
to a published survey, for the reason given above. A survey format could adopt
a response type referring to a governance action directly; if so, this CIP
could be folded into it.

### Security and privacy

- Answers are public and linked to a stake credential. Anyone can see how a
  credential answered, and link that to the addresses and the DRep delegation
  of that credential.
- Credentials are cheap to create ahead of time. A tally SHOULD show the stake
  behind the credentials as a check, so that a large number of answers with
  little stake behind them is visible.
- A record cannot be forged for someone else's credential, since the ledger
  requires the signature of that key.

## Path to Active

### Acceptance Criteria

- [ ] The metadata label is registered in CIP-10.
- [x] A tally implementation reads and counts records by the rules above, and
      its code is public: https://github.com/GS1973/voice-of-ada-holders
      (Apache-2.0).
- [x] Wallets from at least two different vendors have been shown to sign such
      a transaction on mainnet: Eternl, Gero, Lace, Typhon and VESPR, each with
      a real transaction on 2026-09-24.

### Implementation Plan

- [x] Reference implementation: The Voice of ADA Holders
      (https://voiceofadaholders.com), a site that lists the open governance
      actions, builds the transaction, and publishes a tally recountable from
      the chain. Live on mainnet since 2026-09-25.
- [x] Publish the code of the site and of the tally:
      https://github.com/GS1973/voice-of-ada-holders, since 2026-09-25.
- [ ] Register label `1695` in CIP-10 (in the pull request of this CIP).

## Copyright

This CIP is licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).
