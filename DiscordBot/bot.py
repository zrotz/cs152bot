# bot.py
from classifier import classify
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
from Moderator import Moderator_Review
import pdb

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']


class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.reviews = {} # Map from moderator to the state of their review

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)
            
    async def handle_dm(self, message):
        if message.content == Moderator_Review.START_KEYWORD and message.author.name in Moderator_Review.MODERATORS:
            await self.handle_mod_dm(message)
        elif message.author.id in [m.reviewer for m in self.reviews.values()] or message.content in [m.mod_message.jump_url for m in self.reviews.values()]:
            await self.handle_mod_dm(message)
        else:
            await self.handle_user_dm(message)

    async def handle_user_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Let the report class handle this message; forward all the messages it returns to us
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete():
            if message.content.lower() != "cancel":
                await self.handle_reported_message(message.author.name, self.reports[author_id].reported_message, self.reports[author_id].report_info)
            self.reports.pop(author_id)

    
    async def handle_mod_dm(self, message):
        if message.content == Moderator_Review.HELP_KEYWORD:
            reply =  "Use the `review` command to begin the review process.\n"
            reply += "Use the `cancel` command to cancel the review process.\n"
            await message.channel.send(reply)
            return
        elif message.content == Moderator_Review.START_KEYWORD:
            reply =  "Thank you for starting the review process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message from the mod channel that you want to review.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            await message.channel.send(reply)
            return
        elif message.content == Moderator_Review.CANCEL_KEYWORD:
            for m in self.reviews.values():
                if m.reviewer == message.author.id:
                    m.reviewer = None
                    continue
            await message.channel.send("Your review has been cancelled.")
        
        new_review = None
        review = None
        responses = []

        for m in self.reviews.values():
            if m.mod_message.jump_url == message.content:
                new_review = m
                continue

        # If there is no active review, create one
        # Moderator can only be reviewing one post at a time
        if new_review is not None:
            if len([m.reviewer for m in self.reviews.values() if m.reviewer == message.author.id]) == 0:
                self.reviews[new_review.mod_message.id].reviewer = message.author.id
                review = self.reviews[new_review.mod_message.id]
            else:
                await message.channel.send("Another moderator is currently handling this review OR you have not finished a review you started.")
                return
        else:
            # review is already underway
            for m in self.reviews.values():
                if m.reviewer == message.author.id:
                    review = m
                    continue

        # Let the moderator review class handle this message; forward all the messages it returns to us
        responses = await review.handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the review is complete, remove it from our map and the mod channel (which acts as a "to-do" list)
        if review.review_complete():
            await review.mod_message.delete()
            self.reviews.pop(review.mod_message.id)
        
    
    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return
        
        print(message.content)
        print(classify(message.content, "dt"))
        if (classify(message.content, "dt")[0] == 1.0):
            mod_channel = self.mod_channels[message.guild.id]
            mod_message = await mod_channel.send(f'AUTOMATICALLY FLAGGED MESSAGE:\n{message.author.name}: "{message.content}"')
            self.reviews[mod_message.id] = Moderator_Review(self, "AUTOMATED FLAGGING", message, ["hate speech"], mod_message)
            
        # Forward the message to the mod channel
        # mod_channel = self.mod_channels[message.guild.id]
        # await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')
        # scores = self.eval_text(message.content)
        # await mod_channel.send(self.code_format(scores))

    async def handle_reported_message(self, reporting_user, reported_message, report_info):
        # Forward the message to the mod channel
        mod_channel = self.mod_channels[reported_message.guild.id]
        if ("violent threat" in report_info or "dangerous organization or individual" in report_info) and not ("organization" in report_info and "no" in report_info):
            mod_message = await mod_channel.send(f'HIGH PRIORITY!!\nNew user reported message:\n{reported_message.author.name}: "{reported_message.content}"\n\nReporting user is {reporting_user}\nUser reporting flow is: {report_info}')
        else:
            mod_message = await mod_channel.send(f'New user reported message:\n{reported_message.author.name}: "{reported_message.content}"\n\nReporting user is {reporting_user}\nUser reporting flow is: {report_info}')

        self.reviews[mod_message.id] = Moderator_Review(self, reporting_user, reported_message, report_info, mod_message)

        # Used to evaluate classifier later
        # scores = self.eval_text(reported_message.content)
        # await mod_channel.send(self.code_format(scores))

    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    
    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text+ "'"


client = ModBot()
client.run(discord_token)