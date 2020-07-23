# api-channel

The purpose of this repo is to demonstrate a "simplex" channel architecture.

The Inter Government Ledger is designed to be *channel agnostic*, meaning it can support different kinds of channel media for the communication between regulators.

To demonstrate this channel-agnostic concept, multiple types of channel reference implementations have been developed.

Channel implementations can be classified in a variety of ways, for example by the characteristics of the "media" where messages are stored or transmitted:
 * Directionality: Does the channel media carry messages in multiple directions (*Duplex*) or only in one direction (*Simplex*)
 * Centralisation: Is the channel media in one place (*Centralised*) or distributed in more than one place (*Decentralised*)
 * Media Visability: Is access to the channel media restricted (*Private*) or is it visible/transparent (*Public*)

| Directionality | Centralisation | Media Visability | Reference Implementation |
| :----- | :------: | :--------: | --------: |
| Duplex | Decentralised | Public | Etherium Channel |
| Duplex | Decentralised | Private | Hyperledger Channel |
| Duplex | Centralised | Private | DB Channel |
| Simplex | Decentralised | Private | **This API Channel Example** |

This repository demonstrates the Simplex channel pattern.

Each jurisdiction furnishes an API, and expects the other jurisdiction(s) to post messages to it. 
